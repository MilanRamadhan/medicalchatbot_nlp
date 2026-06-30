"""
artifacts.py
Load semua artifact yang dibutuhkan MedicalChatbot SEKALI saat startup
(porting dari notebook Cell 37 "Quick reload dari outputs/").

Kalau file dari Google Drive (model.safetensors, dialog_index.csv,
tfidf_matrix.npz) belum di-download & ditaruh di folder yang benar,
fungsi load_artifacts() akan raise FileNotFoundError dengan pesan
yang jelas file mana yang kurang.
"""

from __future__ import annotations

import json
import logging
import os
import pickle
from dataclasses import dataclass
from typing import Any

import pandas as pd
import scipy.sparse
import torch
from transformers import RobertaForSequenceClassification, RobertaTokenizer

logger = logging.getLogger("medical_chatbot.artifacts")

MAX_LEN = 64

# Folder root project = satu level di atas folder backend/ ini.
# (backend/app/artifacts.py -> backend/app -> backend -> <root>)
BASE_DIR = os.environ.get(
    "MEDCHATBOT_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)
SAVE_DIR = os.path.join(BASE_DIR, "outputs")

REQUIRED_FILES = [
    os.path.join(SAVE_DIR, "roberta_finetuned", "label_mappings.json"),
    # CATATAN: roberta_finetuned/model.safetensors TIDAK diwajibkan — dari folder
    # ini kita cuma butuh tokenizer + label_mappings, bobot modelnya tidak di-load
    # (yang dipakai best_checkpoint/model.safetensors). Mengeluarkannya dari daftar
    # wajib menghemat ~500MB saat deploy. File boleh tetap ada secara lokal.
    os.path.join(SAVE_DIR, "best_checkpoint", "model.safetensors"),
    os.path.join(SAVE_DIR, "dialog_index.csv"),
    os.path.join(SAVE_DIR, "tfidf_vectorizer.pkl"),
    os.path.join(SAVE_DIR, "tfidf_matrix.npz"),
    os.path.join(SAVE_DIR, "disease_symptom_stats.json"),
    os.path.join(SAVE_DIR, "metrics.json"),
]


@dataclass
class Artifacts:
    device: torch.device
    tokenizer: RobertaTokenizer
    model: RobertaForSequenceClassification              # fine-tuned (best_checkpoint)
    base_model: "RobertaForSequenceClassification | None"  # base roberta, untuk perbandingan
    label2id: dict
    id2label: dict
    labels_list: list
    dialog_df: pd.DataFrame
    tfidf: Any
    tfidf_matrix: Any
    disease_symptom_stats: dict
    metrics: dict
    translator: Any = None  # pipeline terjemahan EN->ID (best-effort, boleh None)
    max_len: int = MAX_LEN


def _check_required_files() -> None:
    missing = [f for f in REQUIRED_FILES if not os.path.exists(f)]
    if missing:
        rel = [os.path.relpath(m, BASE_DIR) for m in missing]
        raise FileNotFoundError(
            "Artifact berikut belum ada, download dulu dari Google Drive "
            "sesuai catatan (folder outputs/best_checkpoint & "
            "outputs/roberta_finetuned butuh model.safetensors, "
            "dan outputs/ butuh dialog_index.csv + tfidf_matrix.npz):\n  - "
            + "\n  - ".join(rel)
        )


def load_artifacts() -> Artifacts:
    _check_required_files()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Loading artifacts on device: %s", device)

    with open(os.path.join(SAVE_DIR, "roberta_finetuned", "label_mappings.json")) as f:
        mappings = json.load(f)
    label2id = mappings["label2id"]
    id2label = {int(k): v for k, v in mappings["id2label"].items()}
    labels_list = mappings["labels_list"]
    num_labels = len(labels_list)

    tokenizer = RobertaTokenizer.from_pretrained(
        os.path.join(SAVE_DIR, "roberta_finetuned")
    )

    model = RobertaForSequenceClassification.from_pretrained(
        os.path.join(SAVE_DIR, "best_checkpoint")
    ).to(device)
    model.eval()

    # Model dasar (belum fine-tuned) — dipakai untuk kolom "perbandingan model" di UI.
    # Diunduh dari Hugging Face Hub (roberta-base), bukan dari outputs/.
    # Dibuat best-effort: kalau server tidak ada akses internet ke HF Hub
    # (atau belum ke-cache), backend tetap bisa jalan tanpa kolom perbandingan ini.
    try:
        base_model = RobertaForSequenceClassification.from_pretrained(
            "roberta-base",
            num_labels=num_labels,
            id2label=id2label,
            label2id=label2id,
        ).to(device)
        base_model.eval()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Gagal load base 'roberta-base' dari HF Hub (%s). "
            "Endpoint /chat tetap jalan, hanya kolom 'model dasar' yang kosong.",
            exc,
        )
        base_model = None

    dialog_df = pd.read_csv(os.path.join(SAVE_DIR, "dialog_index.csv"))
    tfidf = pickle.load(open(os.path.join(SAVE_DIR, "tfidf_vectorizer.pkl"), "rb"))
    tfidf_matrix = scipy.sparse.load_npz(os.path.join(SAVE_DIR, "tfidf_matrix.npz"))

    with open(os.path.join(SAVE_DIR, "disease_symptom_stats.json")) as f:
        disease_symptom_stats = json.load(f)
    with open(os.path.join(SAVE_DIR, "metrics.json")) as f:
        metrics = json.load(f)

    # Penerjemah saran medis EN->ID (best-effort). Dipakai agar "Saran medis"
    # dari dataset (aslinya Bahasa Inggris) bisa tampil sesuai bahasa user.
    # Diunduh dari HF Hub sekali (±300MB), lalu di-cache. Kalau gagal (tidak ada
    # internet / sentencepiece belum terpasang), saran tetap Bahasa Inggris.
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        _tr_name = "Helsinki-NLP/opus-mt-en-id"
        _tr_tok = AutoTokenizer.from_pretrained(_tr_name)
        _tr_mdl = AutoModelForSeq2SeqLM.from_pretrained(_tr_name).to(device)
        _tr_mdl.eval()
        translator = (_tr_tok, _tr_mdl)  # dipakai di chatbot._translate_to_id()
        logger.info("Translator EN->ID siap.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Gagal load translator en->id (%s). Saran medis tetap Bahasa Inggris.",
            exc,
        )
        translator = None

    logger.info(
        "Artifacts loaded. %d classes, %d dialogs.", num_labels, len(dialog_df)
    )

    return Artifacts(
        device=device,
        tokenizer=tokenizer,
        model=model,
        base_model=base_model,
        label2id=label2id,
        id2label=id2label,
        labels_list=labels_list,
        dialog_df=dialog_df,
        tfidf=tfidf,
        tfidf_matrix=tfidf_matrix,
        disease_symptom_stats=disease_symptom_stats,
        metrics=metrics,
        translator=translator,
    )
