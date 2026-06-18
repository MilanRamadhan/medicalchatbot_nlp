import type { ChatResponse, LangMode, Metrics, ResetResponse } from "./types";

// Mock layer (PRD Section 12). Toggle with NEXT_PUBLIC_USE_MOCK in .env.local.
// When the backend is ready, set NEXT_PUBLIC_USE_MOCK=false — no other code
// changes are required.
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** POST /chat — send a user message, get a markdown response back. */
export async function sendChat(
  message: string,
  sessionId: string,
  langMode: LangMode,
): Promise<ChatResponse> {
  if (USE_MOCK) return mockChat(message, langMode);

  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      lang_mode: langMode,
    }),
  });
  if (!res.ok) throw new Error("Backend error");
  // Real backend returns { session_id, reply, format, lang, state, diagnosis }.
  // The PRD/mock used { response, lang }. Map `reply` → `response` so the rest
  // of the app stays unchanged; fall back to `response` for forward-compat.
  const data = (await res.json()) as { reply?: string; response?: string; lang?: string };
  return { response: data.reply ?? data.response ?? "", lang: data.lang ?? "id" };
}

/** POST /reset — clear server-side conversation state for this session. */
export async function resetChat(sessionId: string): Promise<ResetResponse> {
  if (USE_MOCK) {
    await delay(200);
    return { status: "ok" };
  }

  const res = await fetch(`${API_URL}/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error("Backend error");
  // Real backend returns { session_id, message }; the app only needs to know
  // the call succeeded, so normalize to { status: "ok" }.
  await res.json().catch(() => null);
  return { status: "ok" };
}

/** GET /metrics — base vs fine-tuned model metrics. */
export async function getMetrics(): Promise<Metrics> {
  if (USE_MOCK) {
    await delay(300);
    return mockMetrics();
  }

  const res = await fetch(`${API_URL}/metrics`);
  if (!res.ok) throw new Error("Backend error");
  return res.json() as Promise<Metrics>;
}

/** Whether the app is currently running against the mock layer. */
export const isMockMode = USE_MOCK;

// ---------------------------------------------------------------------------
// Mock implementations (PRD Section 12.3)
// ---------------------------------------------------------------------------

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function mockMetrics(): Metrics {
  return {
    base: { accuracy: 0.036, f1_macro: 0.004 },
    finetuned: {
      accuracy: 0.867,
      f1_macro: 0.866,
      precision_macro: 0.875,
      recall_macro: 0.866,
    },
    num_classes: 30,
    num_dialogs: 37321,
  };
}

async function mockChat(
  message: string,
  langMode: LangMode,
): Promise<ChatResponse> {
  // Simulate network + model latency so the "typing..." indicator is visible.
  await delay(700);

  const isId =
    langMode === "id" ||
    (langMode === "auto" &&
      /\b(saya|aku|nyeri|sakit|demam|sesak|flu|batuk|pusing|mual)\b/i.test(
        message,
      ));

  if (/halo|hai|hello|hi\b/i.test(message)) {
    return {
      response: isId
        ? "Halo! Saya asisten kesehatan berbasis AI. Ceritakan keluhan atau gejala yang kamu rasakan."
        : "Hello! I'm an AI health assistant. Describe your symptoms.",
      lang: isId ? "id" : "en",
    };
  }

  return {
    response: isId
      ? `**Gejala terdeteksi:** nyeri dada, sesak napas\n\n**Kemungkinan penyakit:** Heart Disease (confidence: 98%)\n\n**3 kemungkinan teratas:**\n  1. Heart Disease — 98%\n  2. Bronchitis — 1%\n  3. Asthma — 0%\n\n**Model dasar (tanpa fine-tuning):** Stroke (4%)\n\n---\n**Saran medis (sumber dataset, EN):** Thanks for your question. Fluttering sensation in chest is commonly seen with arrhythmia.\n\n*⚠️ Hanya untuk edukasi. Silakan konsultasi ke dokter.*`
      : `**Detected symptoms:** chest pain, shortness of breath\n\n**Predicted disease:** Heart Disease (98% confidence)\n\n**Top 3 possibilities:**\n  1. Heart Disease — 98%\n  2. Bronchitis — 1%\n  3. Asthma — 0%\n\n**Base model (no fine-tuning):** Stroke (4%)\n\n---\n**Medical advice:** Thanks for your question. Fluttering sensation in chest is commonly seen with arrhythmia.\n\n*⚠️ Educational purposes only. Please consult a real doctor.*`,
    lang: isId ? "id" : "en",
  };
}
