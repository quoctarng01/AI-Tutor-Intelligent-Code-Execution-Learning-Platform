const LEVEL_LABELS = { 1: "Concept", 2: "Guidance", 3: "Partial", 4: "Walkthrough" };
const LEVEL_COLORS = { 1: "bg-blue-900", 2: "bg-teal-900", 3: "bg-amber-900", 4: "bg-red-900" };

export function HintCard({ level, text }) {
  return (
    <div className={`rounded-lg p-3 ${LEVEL_COLORS[level] ?? "bg-slate-800"}`}>
      <span className="text-xs font-bold text-white/70 uppercase">
        Level {level} · {LEVEL_LABELS[level] ?? "Hint"}
      </span>
      <p className="mt-2 text-sm leading-relaxed text-white/90">{text}</p>
    </div>
  );
}
