/**
 * Submit button component with loading state.
 * Triggers code submission when clicked.
 */

import type { SubmitResponse } from '../../types';

/**
 * Props for the SubmitButton component.
 */
interface SubmitButtonProps {
  /** Callback fired when button is clicked */
  onClick: () => void;
  /** Whether a submission is in progress */
  loading: boolean;
  /** Whether the button should be disabled */
  disabled?: boolean;
}

/**
 * Styled button component for triggering code submission.
 * Shows a loading spinner when submission is in progress.
 * 
 * @param props - SubmitButtonProps
 * @returns The submit button component
 */
export function SubmitButton({ onClick, loading, disabled = false }: SubmitButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className={`
        px-5 py-2 rounded-lg font-medium text-sm transition-all duration-200
        ${
          loading
            ? 'bg-slate-600 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
        }
        text-white shadow-sm
        disabled:opacity-50 disabled:cursor-not-allowed
      `}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Running...
        </span>
      ) : (
        'Run Code'
      )}
    </button>
  );
}
