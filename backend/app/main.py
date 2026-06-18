"""
main.py — Entry point backend FastAPI untuk Medical Chatbot.

Jalankan dengan:
    uvicorn app.main:app --reload --port 8000

Endpoint:
    POST /chat      -> kirim pesan, terima balasan chatbot
    POST /reset      -> reset state percakapan untuk satu session_id
    GET  /metrics     -> angka accuracy/F1 base vs fine-tuned
    GET  /health      -> cek status server & artifact

Catatan desain:
  - State percakapan disimpan per `session_id` di memori proses (dict biasa).
    Cukup untuk skala tugas akhir / demo. Kalau backend di-restart, semua
    sesi hilang (memang demikian — tidak ada DB di scope proyek ini).
  - CORS dibuka untuk origin Next.js dev server (http://localhost:3000).
    Tambahkan origin lain di FRONTEND_ORIGINS kalau deploy ke domain lain.
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .artifacts import Artifacts, load_artifacts
from .chatbot import MedicalChatbot
from .schemas import (
    ChatRequest,
    ChatResponse,
    ChatState,
    DiagnosisResult,
    HealthResponse,
    MetricsResponse,
    ResetRequest,
    ResetResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medical_chatbot.main")

# ── state global proses (diisi di startup) ──────────────────────────────
ARTIFACTS: Artifacts | None = None
ARTIFACTS_ERROR: str | None = None
SESSIONS: Dict[str, MedicalChatbot] = {}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global ARTIFACTS, ARTIFACTS_ERROR
    try:
        ARTIFACTS = load_artifacts()
        ARTIFACTS_ERROR = None
    except Exception as exc:  # noqa: BLE001
        # Server tetap jalan supaya /health bisa kasih tahu masalahnya,
        # tapi /chat akan menolak request sampai artifact lengkap.
        ARTIFACTS = None
        ARTIFACTS_ERROR = str(exc)
        logger.error("Gagal load artifacts: %s", exc)
    yield
    # tidak ada cleanup khusus saat shutdown


# Tambahkan origin frontend lain di sini kalau perlu (mis. domain produksi),
# atau override lewat env var CORS_ORIGINS (dipisah koma).
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
FRONTEND_ORIGINS = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",") if o.strip()
]

app = FastAPI(title="Medical Chatbot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_artifacts() -> Artifacts:
    if ARTIFACTS is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model/artifact belum siap di server. "
                f"Detail: {ARTIFACTS_ERROR or 'unknown error'}"
            ),
        )
    return ARTIFACTS


def _get_or_create_session(session_id: str | None, lang_mode: str | None) -> tuple[str, MedicalChatbot]:
    artifacts = _require_artifacts()
    if session_id and session_id in SESSIONS:
        bot = SESSIONS[session_id]
        if lang_mode in ("auto", "id", "en"):
            bot.lang_mode = lang_mode
        return session_id, bot

    new_id = session_id or str(uuid.uuid4())
    bot = MedicalChatbot(artifacts, lang_mode=lang_mode or "auto")
    SESSIONS[new_id] = bot
    return new_id, bot


# ─────────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if ARTIFACTS is not None else "degraded",
        artifacts_loaded=ARTIFACTS is not None,
        detail=ARTIFACTS_ERROR,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    session_id, bot = _get_or_create_session(req.session_id, req.lang_mode)

    reply_text, diagnosis = bot.chat(req.message)

    diagnosis_model = None
    if diagnosis is not None:
        diagnosis_model = DiagnosisResult(**diagnosis)

    return ChatResponse(
        session_id=session_id,
        reply=reply_text,
        format="markdown",
        lang=bot.lang,
        state=ChatState(
            symptoms=list(bot.symptoms),
            rejected_symptoms=list(bot.rejected),
            pending_confirmation=bot.pending,
            turn=bot.turn,
        ),
        diagnosis=diagnosis_model,
    )


@app.post("/reset", response_model=ResetResponse)
def reset(req: ResetRequest) -> ResetResponse:
    artifacts = _require_artifacts()

    if req.session_id and req.session_id in SESSIONS:
        SESSIONS[req.session_id].reset()
        return ResetResponse(session_id=req.session_id, message="Sesi telah di-reset.")

    new_id = req.session_id or str(uuid.uuid4())
    SESSIONS[new_id] = MedicalChatbot(artifacts)
    return ResetResponse(session_id=new_id, message="Sesi baru dibuat.")


@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    artifacts = _require_artifacts()
    m = artifacts.metrics
    return MetricsResponse(
        base=m["base"],
        finetuned=m["finetuned"],
        num_classes=len(artifacts.labels_list),
        num_dialogs=len(artifacts.dialog_df),
    )
