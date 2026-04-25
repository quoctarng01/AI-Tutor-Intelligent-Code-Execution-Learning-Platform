/**
 * Custom hook for fetching exercise data and tracking solving time.
 * Provides loading states, error handling, and elapsed time tracking.
 */

import { useEffect, useState, useCallback } from 'react';
import { api, getErrorMessage } from '../api/client';
import type { Exercise, UseExerciseReturn } from '../types';

/**
 * Fetches exercise details by ID and provides elapsed time tracking.
 * 
 * @param exerciseId - The unique identifier of the exercise
 * @returns Exercise data, loading state, error message, and elapsed seconds
 * 
 * @example
 * const { exercise, loading, elapsedSeconds } = useExercise(exerciseId);
 */
export function useExercise(exerciseId: string | undefined): UseExerciseReturn {
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!exerciseId) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    let timerId: ReturnType<typeof setInterval> | undefined;

    const fetchExercise = async () => {
      setLoading(true);
      setError(null);
      setElapsedSeconds(0);

      try {
        const { data } = await api.get<Exercise[]>('/exercises');
        if (cancelled) return;

        const matched = data.find((item) => item.id === exerciseId);
        setExercise(matched ?? null);

        if (matched) {
          // Start timer when exercise is loaded
          const startedAt = Date.now();
          timerId = setInterval(() => {
            setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
          }, 1000);
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchExercise();

    return () => {
      cancelled = true;
      if (timerId) {
        clearInterval(timerId);
      }
    };
  }, [exerciseId]);

  return { exercise, loading, error, elapsedSeconds };
}
