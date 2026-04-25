export function SubmitButton({ onClick, loading }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded font-medium text-sm"
    >
      {loading ? "Submitting..." : "Run & Submit"}
    </button>
  );
}
