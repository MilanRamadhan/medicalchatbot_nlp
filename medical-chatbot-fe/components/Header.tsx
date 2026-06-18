import { isMockMode } from "@/lib/api";
import { HealthIcon } from "@/components/Icons";

/** Animated ECG / heartbeat line — health motif, pure SVG (no Lottie dep). */
function EcgLine() {
  return (
    <svg
      viewBox="0 0 200 40"
      className="h-7 w-28"
      fill="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="ecg-grad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#0d9488" />
          <stop offset="50%" stopColor="#06b6d4" />
          <stop offset="100%" stopColor="#3b82f6" />
        </linearGradient>
      </defs>
      <path
        className="ecg-path"
        d="M0,20 L46,20 L54,20 L60,7 L68,33 L75,20 L104,20 L112,20 L118,11 L126,29 L133,20 L200,20"
        stroke="url(#ecg-grad)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * App title, subtitle, and an always-visible education disclaimer (PRD 5.1).
 */
export default function Header() {
  return (
    <header className="fade-up text-center">
      <div className="mb-2 flex items-center justify-center gap-2">
        <span className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-500 shadow-lg shadow-teal-500/30">
          <HealthIcon className="h-6 w-6 text-white" />
        </span>
        <h1 className="gradient-text text-3xl font-extrabold tracking-tight">
          Medical Symptom Chatbot
        </h1>
        {isMockMode && (
          <span className="rounded-full border border-amber-300 bg-amber-100/80 px-2 py-0.5 text-[0.7rem] font-semibold uppercase tracking-wide text-amber-700">
            Mock
          </span>
        )}
      </div>

      <div className="mb-2 flex justify-center">
        <EcgLine />
      </div>

      <p className="shiny-text text-sm font-medium">
        Asisten kesehatan berbasis AI (Bahasa Indonesia &amp; English) —
        klasifikasi 30 penyakit dengan RoBERTa.
      </p>

      <p className="mx-auto mt-3 max-w-xl rounded-xl border border-amber-200/70 bg-amber-50/70 px-3 py-2 text-xs text-amber-800 backdrop-blur-sm">
        ⚠️ Hanya untuk tujuan edukasi dan bukan pengganti diagnosis medis
        profesional. Selalu konsultasikan keluhan kesehatan ke dokter.
      </p>
    </header>
  );
}
