export function ResultBadge({ result }) {
  if (!result) return null;
  return (
    <span className={result.is_correct ? "text-green-400 text-sm" : "text-red-400 text-sm"}>
      {result.is_correct ? "✓ Correct" : "✗ Wrong answer"}
    </span>
  );
}
