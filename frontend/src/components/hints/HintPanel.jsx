import { HintButton } from "./HintButton";
import { HintCard } from "./HintCard";

export function HintPanel({ hints, currentLevel, isExhausted, isLoading, onRequestHint, isSolved }) {
  const hintsRemaining = Math.max(0, 4 - currentLevel);

  return (
    <div className="flex flex-col h-full bg-slate-900">
      <div className="p-4 border-b border-slate-700">
        <h2 className="font-semibold text-sm text-slate-300">HINTS</h2>
        <p className="text-xs text-slate-500 mt-1">
          {isExhausted ? "All hints used" : isSolved ? "Solved!" : `${hintsRemaining} hint(s) remaining`}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {hints.map((h, i) => (
          <HintCard key={`${h.level}-${i}`} level={h.level} text={h.text} />
        ))}
        {hints.length === 0 && (
          <p className="text-slate-500 text-sm text-center mt-8">Stuck? Request a hint to get started.</p>
        )}
      </div>

      <div className="p-4 border-t border-slate-700">
        <HintButton
          onClick={onRequestHint}
          disabled={isExhausted || isSolved || isLoading}
          isLoading={isLoading}
          isExhausted={isExhausted}
          currentLevel={currentLevel}
        />
      </div>
    </div>
  );
}
