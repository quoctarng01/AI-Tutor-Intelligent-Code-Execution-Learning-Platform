import { useCallback, useState } from "react";

import { api } from "../api/client";

export function useHintSystem(sessionId, exerciseId) {
  const [hints, setHints] = useState([]);
  const [currentLevel, setLevel] = useState(0);
  const [isExhausted, setExhausted] = useState(false);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const requestHint = useCallback(async () => {
    if (isExhausted || isLoading) return;
    setLoading(true);
    setError(null);

    try {
      const { data } = await api.post("/hint", {
        session_id: sessionId,
        exercise_id: exerciseId,
      });
      setHints((prev) => [...prev, { level: data.level, text: data.hint }]);
      setLevel(data.level);
      if (data.is_final) setExhausted(true);
    } catch (err) {
      const code = err.response?.data?.detail;
      if (code === "hints_exhausted") setExhausted(true);
      else setError("Failed to load hint. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [sessionId, exerciseId, isExhausted, isLoading]);

  return { hints, currentLevel, isExhausted, isLoading, error, requestHint };
}
