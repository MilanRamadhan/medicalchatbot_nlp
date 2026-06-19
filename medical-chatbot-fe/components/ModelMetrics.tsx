"use client";

import { useEffect, useRef, useState } from "react";
import { getMetrics } from "@/lib/api";
import { DISEASES } from "@/lib/diseases";
import type { Metrics } from "@/lib/types";
import { HealthIcon } from "@/components/Icons";

/** Animate a value from 0 → target with easeOutCubic when `run` becomes true. */
function useCountUp(target: number, run: boolean, duration = 1100): number {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!run) {
      setValue(0);
      return;
    }
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(target * eased);
      if (p < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, run, duration]);

  return value;
}

interface MetricBarProps {
  label: string;
  baseValue: number;
  fineValue: number;
  run: boolean;
}

/** One metric row: animated count-up % + two comparison bars. */
function MetricBar({ label, baseValue, fineValue, run }: MetricBarProps) {
  const base = useCountUp(baseValue, run);
  const fine = useCountUp(fineValue, run);

  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-slate-600">{label}</span>
        <span className="text-sm font-bold tabular-nums text-teal-700">
          {(fine * 100).toFixed(1)}%
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-teal-500 to-cyan-400"
          style={{ width: `${fine * 100}%` }}
        />
      </div>
      <div className="flex items-center gap-2">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-slate-300"
            style={{ width: `${base * 100}%` }}
          />
        </div>
        <span className="w-20 shrink-0 text-right text-[0.7rem] tabular-nums text-slate-400">
          base {(base * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

/**
 * Scope panel: shows the 30 diseases the chatbot can classify (so users know
 * its limits), with the base-vs-finetuned accuracy metrics tucked behind a
 * collapsible toggle (PRD §5.2 still requires showing that comparison).
 */
export default function ModelMetrics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);

  useEffect(() => {
    let active = true;
    getMetrics()
      .then((m) => active && setMetrics(m))
      .catch(() => active && setError(true));
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="fade-up shrink-0 rounded-2xl border border-white/60 bg-white/70 p-4 shadow-xl shadow-teal-900/5 backdrop-blur-xl">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <span className="grid h-6 w-6 place-items-center rounded-lg bg-gradient-to-br from-teal-500 to-cyan-500 shadow-sm shadow-teal-500/30">
            <HealthIcon className="h-4 w-4 text-white" />
          </span>
          Bisa mendeteksi {DISEASES.length} penyakit
        </h2>
        {metrics && (
          <span className="hidden shrink-0 rounded-full bg-cyan-50 px-2 py-0.5 text-xs font-medium text-cyan-700 sm:inline">
            {metrics.num_dialogs.toLocaleString("id-ID")} dialog medis
          </span>
        )}
      </div>

      <p className="mb-2 text-xs text-slate-500">
        Hanya {DISEASES.length} kondisi berikut yang dikenali — sebutkan gejala
        yang relevan:
      </p>

      {/* 30-disease chips (capped height, scrolls internally) */}
      <div className="chat-scroll flex max-h-[4.75rem] flex-wrap gap-1.5 overflow-y-auto pr-1">
        {DISEASES.map((d) => (
          <span
            key={d.en}
            title={d.id}
            className="cursor-default rounded-full border border-teal-100 bg-teal-50/70 px-2 py-0.5 text-[0.7rem] font-medium text-teal-700 transition-colors hover:border-teal-300 hover:bg-teal-100"
          >
            {d.en}
          </span>
        ))}
      </div>

      {/* Collapsible model performance */}
      <div className="mt-3 border-t border-slate-100 pt-2">
        <button
          type="button"
          onClick={() => setShowMetrics((v) => !v)}
          aria-expanded={showMetrics}
          className="flex items-center gap-1.5 text-xs font-medium text-slate-500 transition-colors hover:text-teal-700"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`h-3.5 w-3.5 transition-transform ${showMetrics ? "rotate-90" : ""}`}
          >
            <path d="M9 18l6-6-6-6" />
          </svg>
          Lihat performa model (akurasi base vs fine-tuned)
        </button>

        {showMetrics && (
          <div className="slide-down mt-3">
            {error && (
              <p className="text-sm text-slate-400">
                Metrik tidak tersedia (server tidak terhubung).
              </p>
            )}
            {!metrics && !error && (
              <div className="space-y-3">
                <div className="h-8 w-full animate-pulse rounded bg-slate-100" />
                <div className="h-8 w-full animate-pulse rounded bg-slate-100" />
              </div>
            )}
            {metrics && (
              <div className="grid gap-4 sm:grid-cols-2">
                <MetricBar
                  label="Accuracy"
                  baseValue={metrics.base.accuracy}
                  fineValue={metrics.finetuned.accuracy}
                  run={showMetrics}
                />
                <MetricBar
                  label="Macro F1"
                  baseValue={metrics.base.f1_macro}
                  fineValue={metrics.finetuned.f1_macro}
                  run={showMetrics}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
