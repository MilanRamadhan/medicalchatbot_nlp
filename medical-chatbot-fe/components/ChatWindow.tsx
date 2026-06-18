"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/lib/types";
import ChatBubble from "./ChatBubble";
import { RobotFace, RobotMascot } from "@/components/Icons";

interface ChatWindowProps {
  messages: Message[];
  loading: boolean;
}

/**
 * Scrollable message area. Auto-scrolls to the bottom whenever a new message
 * arrives or the typing indicator toggles (PRD 5.4).
 */
export default function ChatWindow({ messages, loading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const isEmpty = messages.length === 0;

  return (
    <div className="chat-scroll flex-1 space-y-3 overflow-y-auto px-4 py-5">
      {isEmpty && !loading && (
        <div className="flex h-full min-h-[180px] flex-col items-center justify-center text-center text-slate-400 pop-in">
          <div className="relative grid place-items-center">
            <span
              aria-hidden="true"
              className="absolute h-24 w-24 rounded-full bg-teal-400/25 blur-2xl"
              style={{ animation: "robot-glow 3s ease-in-out infinite" }}
            />
            <RobotMascot className="relative h-28 w-28" />
          </div>
          <p className="mt-3 max-w-xs text-sm">
            Hai! Aku asisten kesehatanmu. Ceritakan gejalamu, atau pilih salah
            satu contoh di bawah.
          </p>
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
