/**
 * Custom hook for managing the 4-level progressive hint system.
 * Handles hint requests, state management, and error handling.
 */

import { useState, useCallback } from 'react';
import { api, getErrorMessage, isNetworkError } from '../api/client';
import type {
  Hint,
  UseHintSystemReturn,
} from '../types';

interface UseHintSystemOptions {
  sessionId: string | null;
  exerciseId: string;
}

/**
 * Manages hint system state and requests.
 * 
 * @param options - Configuration including sessionId and exerciseId
 * @returns Hint system state and request function
 * 
 * @example
 * const { hints, currentLevel, requestHint, isExhausted } = useHintSystem({
 *   sessionId: 'uuid',
 *   exerciseId: 'exercise-1'
 * });
 */
export function useHintSystem({
  sessionId,
  exerciseId,
}: UseHintSystemOptions): UseHintSystemReturn {
  const [hints, setHints] = useState<Hint[]>([]);
  const [currentLevel, setLevel] = useState(0);
  const [isExhausted, setExhausted] = useState(false);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestHint = useCallback(async () => {
    if (isExhausted || isLoading || !sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const { data } = await api.post<{ level: number; hint: string; is_final: boolean }>(
        '/hint/',
        {
          session_id: sessionId,
          exercise_id: exerciseId,
        },
        {
          timeout: 30000, // Longer timeout for LLM hints
        }
      );

      setHints((prev) => [...prev, { level: data.level, text: data.hint }]);
      setLevel(data.level);
      if (data.is_final) setExhausted(true);
    } catch (err) {
      const errorMessage = getErrorMessage(err);

      // Check for specific error codes
      if (isNetworkError(err)) {
        setError('Network error. Please check your connection.');
      } else if (errorMessage.includes('hints_exhausted')) {
        setExhausted(true);
      } else if (errorMessage.includes('exercise_already_solved')) {
        setError('Exercise already solved!');
      } else {
        setError('Failed to load hint. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [sessionId, exerciseId, isExhausted, isLoading]);

  return {
    hints,
    currentLevel,
    isExhausted,
    isLoading,
    error,
    requestHint,
  };
}
