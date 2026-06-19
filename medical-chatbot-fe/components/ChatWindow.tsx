"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/lib/types";
import ChatBubble from "./ChatBubble";
import QuickPrompts from "./QuickPrompts";
import { RobotFace, RobotMascot } from "@/components/Icons";

interface ChatWindowProps {
  messages: Message[];
  loading: boolean;
  onQuickPrompt: (text: string) => void;
}

/**
 * Scrollable message area. Auto-scrolls to the bottom whenever a new message
 * arrives or the typing indicator toggles (PRD 5.4). When empty, shows the
 * welcome mascot + quick-prompt chips (inside the scroll area, so the page
 * itself never grows — only this region scrolls).
 */
export default function ChatWindow({
  messages,
  loading,
  onQuickPrompt,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const isEmpty = messages.length === 0;

  return (
    <div className="chat-scroll min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4">
      {isEmpty && !loading && (
        <div className="flex min-h-full flex-col items-center justify-center gap-3 py-2 text-center text-slate-400 pop-in">
          <div className="flex flex-col items-center">
            <div className="relative grid place-items-center">
              <span
                aria-hidden="true"
                className="absolute h-14 w-14 rounded-full bg-teal-400/25 blur-2xl"
                style={{ animation: "robot-glow 3s ease-in-out infinite" }}
              />
              <RobotMascot className="relative h-20 w-20" />
            </div>
            <p className="mt-1.5 max-w-xs text-sm">
              Hai! Aku asisten kesehatanmu. Ceritakan gejalamu, atau pilih
              salah satu contoh di bawah.
            </p>
          </div>
          <QuickPrompts onSelect={onQuickPrompt} disabled={loading} />
        </div>
      )}

      {messages.map((msg, i) => (
        <ChatBubble key={i} role={msg.role} content={msg.content} />
      ))}

      {loading && (
        <div className="flex items-start gap-2 bubble-in">
          <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-teal-500 to-cyan-500 shadow-md shadow-teal-500/30">
            <RobotFace className="h-5 w-5 text-white" />
          </span>
          <div className="rounded-2xl rounded-bl-md border border-white/70 bg-white/80 px-4 py-3.5 shadow-lg shadow-slate-900/5 backdrop-blur-md">
            <span className="sr-only">Bot sedang mengetik…</span>
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
