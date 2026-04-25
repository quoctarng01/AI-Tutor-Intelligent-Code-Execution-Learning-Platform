import type { Hint } from '../../types';

interface HintPanelProps {
  hints: Hint[];
  currentLevel: number;
  isExhausted: boolean;
  isLoading: boolean;
  onRequestHint: () => void;
  isSolved?: boolean;
}

export function HintPanel({
  hints,
  currentLevel,
  isExhausted,
  isLoading,
  onRequestHint,
  isSolved,
}: HintPanelProps) {
  const getHintLevelLabel = (level: number): string => {
    const labels: Record<number, string> = {
      1: 'Concept Reminder',
      2: 'Reasoning Guide',
      3: 'Partial Explanation',
      4: 'Walkthrough',
    };
    return labels[level] || `Level ${level}`;
  };

  const getHintLevelColor = (level: number): string => {
    const colors: Record<number, string> = {
      1: 'bg-blue-600/20 text-blue-400 border-blue-600/30',
      2: 'bg-purple-600/20 text-purple-400 border-purple-600/30',
      3: 'bg-amber-600/20 text-amber-400 border-amber-600/30',
      4: 'bg-red-600/20 text-red-400 border-red-600/30',
    };
    return colors[level] || 'bg-slate-600/20 text-slate-400 border-slate-600/30';
  };

  return (
    <div className="h-full bg-slate-800 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200">Hints</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">
            Level: <span className="text-white font-medium">{currentLevel}/4</span>
          </span>
        </div>
      </div>

      {/* Hint Content */}
      <div className="flex-1 overflow-auto p-4">
        {hints.length === 0 ? (
          <div className="text-center text-slate-400 py-8">
            <p className="text-sm mb-4">No hints requested yet.</p>
            <p className="text-xs text-slate-500">
              Click the button below to get a hint.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {hints.map((hint) => (
              <div
                key={hint.level}
                className={`p-3 rounded-lg border ${getHintLevelColor(hint.level)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium uppercase tracking-wide">
                    {getHintLevelLabel(hint.level)}
                  </span>
                  <span className="text-xs opacity-60">L{hint.level}</span>
                </div>
                <p className="text-sm leading-relaxed">{hint.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Hint Button */}
      <div className="p-4 border-t border-slate-700">
        {isSolved ? (
          <div className="text-center py-2">
            <span className="text-green-400 text-sm font-medium">
              Exercise completed!
            </span>
          </div>
        ) : isExhausted ? (
          <div className="text-center py-2">
            <span className="text-slate-400 text-sm">
              All hints exhausted
            </span>
          </div>
        ) : (
          <button
            onClick={onRequestHint}
            disabled={isLoading}
            className={`
              w-full py-2.5 px-4 rounded-lg font-medium text-sm transition-all duration-200
              ${
                isLoading
                  ? 'bg-slate-700 cursor-not-allowed text-slate-400'
                  : 'bg-slate-700 hover:bg-slate-600 text-white'
              }
            `}
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Getting hint...
              </span>
            ) : (
              `Get Hint ${currentLevel + 1}`
            )}
          </button>
        )}
      </div>
    </div>
  );
}
