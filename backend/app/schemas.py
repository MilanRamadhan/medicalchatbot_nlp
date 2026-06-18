"""schemas.py — Pydantic models untuk request & response API."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Pesan dari user")
    session_id: Optional[str] = Field(
        None, description="ID sesi. Kosongkan di pesan pertama, backend akan generate."
    )
    lang_mode: Optional[str] = Field(
        None, description="'auto' (default) | 'id' | 'en' — override bahasa untuk sesi ini"
    )


class Top3Item(BaseModel):
    disease: str
    probability: float


class DiagnosisResult(BaseModel):
    predicted_disease: Optional[str]
    confidence: float
    top3: List[Top3Item]
    base_model_prediction: Optional[str]
    base_model_confidence: float
    advice: Optional[str]
    symptoms: List[str]


class ChatState(BaseModel):
    symptoms: List[str]
    rejected_symptoms: List[str]
    pending_confirmation: Optional[str]
    turn: int


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    format: str = "markdown"  # field ini menandakan `reply` berisi markdown, bukan plain text
    lang: str  # 'id' | 'en'
    state: ChatState
    diagnosis: Optional[DiagnosisResult] = None  # terisi hanya saat chatbot memberi diagnosis


class ResetRequest(BaseModel):
    session_id: Optional[str] = None


class ResetResponse(BaseModel):
    session_id: str
    message: str


class ModelMetrics(BaseModel):
    accuracy: float
    f1_macro: float
    precision_macro: Optional[float] = None
    recall_macro: Optional[float] = None


class MetricsResponse(BaseModel):
    base: ModelMetrics
    finetuned: ModelMetrics
    num_classes: int
    num_dialogs: int


class HealthResponse(BaseModel):
    status: str
    artifacts_loaded: bool
    detail: Optional[str] = None
