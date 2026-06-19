"use client";

interface QuickPromptsProps {
  onSelect: (text: string) => void;
  disabled?: boolean;
}

// Mix of Indonesian and English examples (PRD 5.6).
const PROMPTS = [
  "saya nyeri dada dan sesak napas",
  "I feel anxious and can't sleep",
  "saya flu sejak 3 hari",
  "saya demam tinggi dan pusing",
  "I have a sore throat and cough",
  "halo",
];

/**
 * Example prompt chips, shown inside the empty-state welcome. Clicking one
 * immediately sends it as a message.
 */
export default function QuickPrompts({
  onSelect,
  disabled,
}: QuickPromptsProps) {
  return (
    <div className="w-full max-w-md">
      <p className="mb-2 text-center text-xs font-medium text-slate-400">
        💡 Contoh pertanyaan:
      </p>
      <div className="flex flex-wrap justify-center gap-1.5">
        {PROMPTS.map((prompt, i) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelect(prompt)}
            disabled={disabled}
            style={{ animationDelay: `${i * 60}ms` }}
            className="fade-up rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs text-slate-600 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-teal-300 hover:bg-gradient-to-r hover:from-teal-50 hover:to-cyan-50 hover:text-teal-700 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-teal-500/30 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
