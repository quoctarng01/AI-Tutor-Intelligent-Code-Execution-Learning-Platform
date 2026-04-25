export function ProgressBar({ completed = 0, total = 0 }) {
  const ratio = total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : 0;
  return (
    <div className="w-full">
      <div className="w-full h-2 rounded bg-slate-700 overflow-hidden">
        <div className="h-full bg-emerald-500" style={{ width: `${ratio}%` }} />
      </div>
      <p className="text-xs text-slate-400 mt-1">
        {completed} / {total} completed
      </p>
    </div>
  );
}
