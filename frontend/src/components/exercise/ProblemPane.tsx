/**
 * Displays the exercise problem statement with metadata.
 * Shows title, topic, difficulty level, and the problem description.
 */

import type { Exercise } from '../../types';

/**
 * Props for the ProblemPane component.
 */
interface ProblemPaneProps {
  /** The exercise to display, or null if no exercise selected */
  exercise: Exercise | null;
}

/**
 * Problem display component showing exercise details and instructions.
 * Renders the problem statement, topic tags, and difficulty indicator.
 * 
 * @param props - ProblemPaneProps containing the exercise data
 * @returns The problem pane component
 */
export function ProblemPane({ exercise }: ProblemPaneProps) {
  if (!exercise) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-800 text-slate-400">
        <p>No exercise selected</p>
      </div>
    );
  }

  return (
    <div className="h-full bg-slate-800 p-4 overflow-auto">
      <div className="mb-3">
        <h2 className="text-lg font-semibold text-white mb-1">{exercise.title}</h2>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="px-2 py-0.5 bg-slate-700 rounded capitalize">{exercise.topic}</span>
          {exercise.difficulty && (
            <span className="px-2 py-0.5 bg-amber-600/20 text-amber-400 rounded">
              Difficulty: {exercise.difficulty}/5
            </span>
          )}
        </div>
      </div>
      <div className="text-sm text-slate-300 whitespace-pre-wrap">
        {exercise.problem_statement}
      </div>
    </div>
  );
}
