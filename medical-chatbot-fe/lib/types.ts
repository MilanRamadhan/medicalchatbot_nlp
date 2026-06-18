// Shared types for the Medical Symptom Chatbot frontend.

export type Role = "user" | "bot";

export interface Message {
  role: Role;
  content: string;
}

export type LangMode = "auto" | "id" | "en";

/** Response shape of POST /chat (PRD Section 3). */
export interface ChatResponse {
  response: string; // markdown
  lang: string; // "id" | "en"
}

/** Response shape of POST /reset. */
export interface ResetResponse {
  status: string;
}

/** Response shape of GET /metrics (PRD Section 3). */
export interface Metrics {
  base: {
    accuracy: number;
    f1_macro: number;
  };
  finetuned: {
    accuracy: number;
    f1_macro: number;
    precision_macro: number;
    recall_macro: number;
  };
  num_classes: number;
  num_dialogs: number;
}
