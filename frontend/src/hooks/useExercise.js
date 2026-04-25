import { useEffect, useState } from "react";

import { api } from "../api/client";

export function useExercise(exerciseId) {
  const [exercise, setExercise] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setElapsedSeconds(0);

    api
      .get("/exercises")
      .then(({ data }) => {
        if (cancelled) return;
        const matched = data.find((item) => item.id === exerciseId);
        setExercise(matched ?? null);
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load exercise");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [exerciseId]);

  useEffect(() => {
    if (!exercise) return undefined;
    const startedAt = Date.now();
    const timer = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [exercise]);

  return { exercise, loading, error, elapsedSeconds };
}
