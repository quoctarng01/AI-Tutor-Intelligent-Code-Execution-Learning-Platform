/**
 * Displays the result of a code submission.
 * Shows a success or failure badge based on the submission result.
 */

import type { SubmitResponse } from '../../types';

/**
 * Props for the ResultBadge component.
 */
interface ResultBadgeProps {
  /** The submission result to display, or null if no result yet */
  result: SubmitResponse | null;
}

/**
 * Badge component showing the outcome of a code submission.
 * Displays a green checkmark for correct submissions and red X for incorrect ones.
 * 
 * @param props - ResultBadgeProps containing the submission result
 * @returns The result badge component, or null if no result
 */
export function ResultBadge({ result }: ResultBadgeProps) {
  if (!result) {
    return null;
  }

  return (
    <div
      className={`
        px-3 py-1 rounded-full text-sm font-medium
        ${
          result.is_correct
            ? 'bg-green-600/20 text-green-400 border border-green-600/30'
            : 'bg-red-600/20 text-red-400 border border-red-600/30'
        }
      `}
    >
      {result.is_correct ? (
        <span className="flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Correct!
        </span>
      ) : (
        <span className="flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          Incorrect
        </span>
      )}
    </div>
  );
}
