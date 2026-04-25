export function HintButton({ onClick, disabled, isLoading, isExhausted, currentLevel }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full py-2 rounded bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-sm font-medium transition-colors"
    >
      {isLoading ? "Loading..." : isExhausted ? "No hints remaining" : `Get Hint (Level ${currentLevel + 1})`}
    </button>
  );
}
