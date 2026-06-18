"use client";

import { useEffect, useRef, useState } from "react";
import { getMetrics } from "@/lib/api";
import type { Metrics } from "@/lib/types";

/** Animate a value from 0 → target with easeOutCubic when `run` becomes true. */
function useCountUp(target: number, run: boolean, duration = 1100): number {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!run) return;
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

      {/* Fine-tuned bar (gradient) */}
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-teal-500 to-cyan-400"
          style={{ width: `${fine * 100}%` }}
        />
      </div>

      {/* Base bar (muted, thin) */}
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
 * Card comparing base vs fine-tuned RoBERTa on Accuracy and Macro F1, with
 * animated count-up numbers and gradient bars. Fetched once on mount (PRD 5.2).
 */
export default function ModelMetrics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    getMetrics()
      .then((m) => active && setMetrics(m))
      .catch(() => active && setError(true));
    return () => {
      active = false;
    };
  }, []);

  const ready = metrics !== null;

  return (
    <section className="fade-up rounded-2xl border border-white/60 bg-white/70 p-5 shadow-xl shadow-teal-900/5 backdrop-blur-xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <span className="h-2 w-2 animate-pulse rounded-full bg-teal-500" />
          Performa Model — RoBERTa
        </h2>
        {metrics && (
          <div className="flex items-center gap-1.5 text-xs">
            <span className="rounded-full bg-teal-50 px-2 py-0.5 font-medium text-teal-700">
              {metrics.num_classes} penyakit
            </span>
            <span className="rounded-full bg-cyan-50 px-2 py-0.5 font-medium text-cyan-700">
              {metrics.num_dialogs.toLocaleString("id-ID")} dialog
            </span>
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-slate-400">
          Metrik tidak tersedia (server tidak terhubung).
        </p>
      )}

      {!metrics && !error && (
        <div className="space-y-4">
          <div className="h-8 w-full animate-pulse rounded bg-slate-100" />
          <div className="h-8 w-full animate-pulse rounded bg-slate-100" />
        </div>
      )}

      {metrics && (
        <div className="grid gap-5 sm:grid-cols-2">
          <MetricBar
            label="Accuracy"
            baseValue={metrics.base.accuracy}
            fineValue={metrics.finetuned.accuracy}
            run={ready}
          />
          <MetricBar
            label="Macro F1"
            baseValue={metrics.base.f1_macro}
            fineValue={metrics.finetuned.f1_macro}
            run={ready}
          />
        </div>
      )}
    </section>
  );
}
