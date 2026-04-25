import { useState } from "react";

const ChevronUpIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m18 15-6-6-6 6"/>
  </svg>
);

const ChevronDownIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m6 9 6 6 6-6"/>
  </svg>
);

export function ProblemPane({ exercise, defaultCollapsed = false }) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  if (collapsed) {
    return (
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-200">{exercise?.title}</span>
          <span className="text-xs text-slate-500">
            {exercise?.topic} · {exercise?.difficulty}
          </span>
        </div>
        <button
          onClick={() => setCollapsed(false)}
          className="p-1 hover:bg-slate-700 rounded text-slate-400 hover:text-slate-200 transition-colors"
          title="Expand problem"
        >
          <ChevronDownIcon />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-900">
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-slate-200">{exercise?.title}</span>
          <span className="text-xs px-2 py-0.5 bg-slate-700 rounded text-slate-400">
            {exercise?.difficulty}
          </span>
          <span className="text-xs text-slate-500">
            {exercise?.topic} {exercise?.subtopic ? `· ${exercise.subtopic}` : ""}
          </span>
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="p-1 hover:bg-slate-700 rounded text-slate-400 hover:text-slate-200 transition-colors"
          title="Collapse problem"
        >
          <ChevronUpIcon />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        <p className="text-sm leading-relaxed text-slate-200 whitespace-pre-wrap">
          {exercise?.problem_statement}
        </p>
        {exercise?.concept ? (
          <p className="mt-3 text-xs text-slate-400">
            Concept focus: <span className="text-slate-300">{exercise.concept}</span>
          </p>
        ) : null}
      </div>
    </div>
  );
}
