"use client";

import { useEffect, useState } from "react";
import { resetChat, sendChat } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import type { LangMode, Message } from "@/lib/types";
import Header from "@/components/Header";
import ModelMetrics from "@/components/ModelMetrics";
import LanguageSelector from "@/components/LanguageSelector";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";

export default function Home() {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [langMode, setLangMode] = useState<LangMode>("auto");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [lastUserMessage, setLastUserMessage] = useState<string | null>(null);

  // Resolve (or create) the persisted session id on the client (PRD Section 6).
  useEffect(() => {
    setSessionId(getSessionId());
  }, []);

  /** Call the backend for `text` and append the bot reply. Does not append a
   *  user bubble — used both for fresh sends and for retries. */
  async function deliver(text: string) {
    setLoading(true);
    setError(false);
    try {
      const res = await sendChat(text, sessionId, langMode);
      setMessages((prev) => [...prev, { role: "bot", content: res.response }]);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  function handleSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setLastUserMessage(trimmed);
    void deliver(trimmed);
  }

  function handleRetry() {
    if (lastUserMessage && !loading) void deliver(lastUserMessage);
  }

  async function handleReset() {
    if (loading) return;
    try {
      await resetChat(sessionId);
    } catch {
      // Even if the server reset fails, clear the local conversation.
    }
    setMessages([]);
    setError(false);
    setLastUserMessage(null);
  }

  return (
    <>
      {/* Aurora background (reactbits-style) */}
      <div className="aurora" aria-hidden="true">
        <span className="aurora-blob b1" />
        <span className="aurora-blob b2" />
        <span className="aurora-blob b3" />
      </div>

      <main className="mx-auto flex h-[100dvh] w-full max-w-[760px] flex-col gap-3 overflow-hidden px-4 py-5">
        <Header />
        <ModelMetrics />

        {/* Chat card */}
        <section
          className="fade-up flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-white/60 bg-white/60 shadow-2xl shadow-teal-900/10 backdrop-blur-xl"
          style={{ animationDelay: "120ms" }}
        >
          {/* Controls */}
          <div className="flex items-center justify-between gap-2 border-b border-white/60 bg-white/50 px-3 py-2.5 backdrop-blur-md">
            <LanguageSelector
              value={langMode}
              onChange={setLangMode}
              disabled={loading}
            />
            <button
              type="button"
              onClick={handleReset}
              disabled={loading || messages.length === 0}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-slate-500 transition-colors hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-slate-500"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4"
              >
                <path d="M3 12a9 9 0 109-9 9 9 0 00-6.36 2.64L3 8" />
                <path d="M3 3v5h5" />
              </svg>
              Reset
            </button>
          </div>

          {/* Error banner (PRD UI states) */}
          {error && (
            <div className="slide-down flex items-center justify-between gap-3 border-b border-red-200 bg-red-50/90 px-4 py-2.5 text-sm text-red-700 backdrop-blur-sm">
              <span>⚠️ Tidak dapat terhubung ke server.</span>
              <button
                type="button"
                onClick={handleRetry}
                disabled={loading || !lastUserMessage}
                className="shrink-0 rounded-lg bg-red-600 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
              >
                Coba lagi
              </button>
            </div>
          )}

          <ChatWindow
            messages={messages}
            loading={loading}
            onQuickPrompt={handleSend}
          />

          <ChatInput onSend={handleSend} disabled={loading} />
        </section>

        <footer className="shrink-0 text-center text-xs text-slate-400">
          Kelompok 15 · SINF6054 · Pemrosesan Bahasa Alami
        </footer>
      </main>
    </>
  );
}
