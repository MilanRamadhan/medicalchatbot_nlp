"use client";

import type { LangMode } from "@/lib/types";

interface LanguageSelectorProps {
  value: LangMode;
  onChange: (value: LangMode) => void;
  disabled?: boolean;
}

/**
 * Auto / Indonesia / English dropdown. The selected value is sent as
 * `lang_mode` on every /chat request (PRD 5.3).
 */
export default function LanguageSelector({
  value,
  onChange,
  disabled,
}: LanguageSelectorProps) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-600">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-4 w-4 text-teal-500"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
      </svg>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as LangMode)}
        disabled={disabled}
        aria-label="Pilih bahasa"
        className="cursor-pointer rounded-lg border border-slate-200 bg-white/80 px-2.5 py-1.5 text-sm text-slate-700 shadow-sm transition-colors hover:border-teal-300 focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 disabled:opacity-60"
      >
        <option value="auto">Auto (deteksi)</option>
        <option value="id">Indonesia</option>
        <option value="en">English</option>
      </select>
    </label>
  );
}
