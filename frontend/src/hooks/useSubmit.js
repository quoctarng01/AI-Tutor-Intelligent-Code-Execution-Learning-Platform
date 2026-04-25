import { useState } from "react";

import { api } from "../api/client";

export function useSubmit(sessionId, exerciseId) {
  const [code, setCode] = useState("# Write your solution here\n");
  const [result, setResult] = useState(null);
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (sourceCode, currentHintLevel, elapsedSeconds = null) => {
    if (isSubmitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const { data } = await api.post("/submit", {
        session_id: sessionId,
        exercise_id: exerciseId,
        code: sourceCode,
        language_id: 71,
        elapsed_seconds: elapsedSeconds,
      });
      setResult(data);
      return data;
    } catch (_err) {
      setError("Submission failed. Please retry.");
      const fallback = { is_correct: false, hints_used: currentHintLevel };
      setResult(fallback);
      return fallback;
    } finally {
      setSubmitting(false);
    }
  };

  return { submit, result, code, setCode, isSubmitting, error };
}
