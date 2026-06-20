"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

/**
 * Text input + Send button. Enter submits; the field is disabled while a
 * response is pending (PRD 5.5). The field auto-focuses on mount and re-focuses
 * after each reply finishes, so the user can keep typing without clicking back
 * into it.
 */
export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus on mount and whenever the input becomes enabled again (i.e. right
  // after a bot reply arrives). The disabled field blurs during loading.
  useEffect(() => {
    if (!disabled) inputRef.current?.focus();
  }, [disabled]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
  }

  const canSend = !disabled && value.trim().length > 0;

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2 border-t border-white/60 bg-white/60 px-3 py-3 backdrop-blur-md"
    >
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        autoFocus
        placeholder="Ceritakan gejala kamu / Describe your symptoms…"
        aria-label="Pesan"
        className="flex-1 rounded-full border border-slate-200 bg-white/80 px-4 py-2.5 text-[0.925rem] text-slate-800 shadow-sm transition-all placeholder:text-slate-400 focus:border-teal-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-teal-500/15 disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={!canSend}
        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-cyan-500 text-white transition-all duration-200 hover:scale-105 hover:from-teal-600 hover:to-cyan-600 active:scale-95 focus:outline-none disabled:cursor-not-allowed disabled:from-slate-300 disabled:to-slate-300 disabled:shadow-none ${
          canSend ? "glow-teal" : ""
        }`}
        aria-label="Kirim"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-5 w-5"
        >
          <path d="M3.4 20.4l17.45-7.48a1 1 0 000-1.84L3.4 3.6a.993.993 0 00-1.39.91L2 9.12c0 .5.37.93.87.99L17 12 2.87 13.88c-.5.07-.87.5-.87 1l.01 4.61c0 .71.73 1.2 1.39.91z" />
        </svg>
      </button>
    </form>
  );
}
