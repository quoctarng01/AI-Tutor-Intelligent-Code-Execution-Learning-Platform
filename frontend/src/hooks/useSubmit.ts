/**
 * Custom hook for submitting code to the backend execution engine.
 * Manages submission state, error handling, and result tracking.
 */

import { useState, useCallback } from 'react';
import { api, getErrorMessage, isNetworkError } from '../api/client';
import type { SubmitResponse, UseSubmitReturn } from '../types';

interface UseSubmitOptions {
  sessionId: string | null;
  exerciseId: string;
}

/**
 * Handles code submission to the backend for evaluation.
 * 
 * @param options - Configuration including sessionId and exerciseId
 * @returns Submit function, result state, code state, and loading/error states
 * 
 * @example
 * const { submit, result, code, setCode, isSubmitting } = useSubmit({
 *   sessionId: 'uuid',
 *   exerciseId: 'exercise-1'
 * });
 * 
 * // Submit code for evaluation
 * const response = await submit(userCode, currentHintLevel, elapsedSeconds);
 */
export function useSubmit({
  sessionId,
  exerciseId,
}: UseSubmitOptions): UseSubmitReturn {
  const [code, setCode] = useState('# Write your solution here\n');
  const [result, setResult] = useState<SubmitResponse | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (
      sourceCode: string,
      currentHintLevel: number,
      elapsedSeconds: number | null = null
    ): Promise<SubmitResponse | null> => {
      if (isSubmitting || !sessionId) return null;

      setSubmitting(true);
      setError(null);

      try {
        const { data } = await api.post<SubmitResponse>('/submit', {
          session_id: sessionId,
          exercise_id: exerciseId,
          code: sourceCode,
          language_id: 71, // Python 3 (Judge0 language ID)
          elapsed_seconds: elapsedSeconds,
        });

        setResult(data);
        return data;
      } catch (err) {
        const errorMessage = getErrorMessage(err);

        if (isNetworkError(err)) {
          setError('Network error. Please check your connection.');
        } else {
          setError('Submission failed. Please try again.');
        }

        // Set fallback result so UI can still show feedback
        const fallback: SubmitResponse = {
          is_correct: false,
          hints_used: currentHintLevel,
        };
        setResult(fallback);
        return fallback;
      } finally {
        setSubmitting(false);
      }
    },
    [sessionId, exerciseId, isSubmitting]
  );

  return { submit, result, code, setCode, isSubmitting, error };
}
