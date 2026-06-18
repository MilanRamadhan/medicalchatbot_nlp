import ReactMarkdown from "react-markdown";
import type { Role } from "@/lib/types";
import { RobotFace } from "@/components/Icons";

interface ChatBubbleProps {
  role: Role;
  content: string;
}

/** Small gradient avatar for the bot. */
function BotAvatar() {
  return (
    <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-teal-500 to-cyan-500 shadow-md shadow-teal-500/30">
      <RobotFace className="h-5 w-5 text-white" />
    </span>
  );
}

/**
 * A single message bubble.
 * - user: right-aligned, teal→cyan gradient (primary)
 * - bot:  left-aligned, frosted-glass card, content rendered as markdown
 */
export default function ChatBubble({ role, content }: ChatBubbleProps) {
  const isUser = role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end bubble-in">
        <div className="max-w-[80%] rounded-2xl rounded-br-md bg-gradient-to-br from-teal-600 to-cyan-500 px-4 py-2.5 text-[0.925rem] leading-relaxed text-white shadow-lg shadow-teal-500/25">
          <p className="whitespace-pre-wrap break-words">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start justify-start gap-2 bubble-in">
      <BotAvatar />
      <div className="max-w-[84%] rounded-2xl rounded-bl-md border border-white/70 bg-white/80 px-4 py-3 text-slate-800 shadow-lg shadow-slate-900/5 backdrop-blur-md">
        <div className="markdown-body">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
