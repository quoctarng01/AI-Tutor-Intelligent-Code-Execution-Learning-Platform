/**
 * Main exercise page component.
 * Displays the problem statement, code editor, and hint panel for a single exercise.
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CodeEditor } from '../components/exercise/CodeEditor';
import { ProblemPane } from '../components/exercise/ProblemPane';
import { ResultBadge } from '../components/exercise/ResultBadge';
import { SubmitButton } from '../components/exercise/SubmitButton';
import { HintPanel } from '../components/hints/HintPanel';
import { useExercise } from '../hooks/useExercise';
import { useHintSystem } from '../hooks/useHintSystem';
import { useSubmit } from '../hooks/useSubmit';

/**
 * ExercisePage renders the main coding interface for an exercise.
 * Includes problem display, code editor, submission, and hint system.
 * 
 * @returns The exercise page component
 */
export default function ExercisePage() {
  const { exerciseId } = useParams<{ exerciseId: string }>();
  const navigate = useNavigate();

  // Get session from localStorage
  const sessionId = localStorage.getItem('session_id');
  const username = localStorage.getItem('username');

  const { exercise, loading, elapsedSeconds } = useExercise(exerciseId);
  const hintSystem = useHintSystem({ sessionId, exerciseId: exerciseId || '' });
  const { submit, result, code, setCode, isSubmitting } = useSubmit({
    sessionId,
    exerciseId: exerciseId || '',
  });

  /**
   * Handles code submission.
   */
  const handleSubmit = () => {
    submit(code, hintSystem.currentLevel, elapsedSeconds);
  };

  /**
   * Navigates to the next exercise.
   */
  const handleNextExercise = () => {
    if (exerciseId) {
      navigate(`/exercise/${exerciseId}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900 text-slate-200">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg">Loading exercise...</p>
        </div>
      </div>
    );
  }

  if (!exercise) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900 text-slate-200">
        <div className="text-center">
          <p className="text-xl mb-4">Exercise not found</p>
          <button
            onClick={() => navigate('/topics')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Go to Topics
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-200">
      {/* Top Bar */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-slate-700 bg-slate-800 flex-shrink-0">
        <div className="text-sm text-slate-300">
          User: <span className="text-white font-medium">{username || 'anonymous'}</span>
        </div>
        <div className="text-sm text-slate-400">
          Topic: <span className="text-slate-300">{exercise.topic}</span>
        </div>
        <div className="text-sm text-slate-300">
          {result?.is_correct ? 1 : 0} / 1 complete
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 min-h-0">
        {/* Left Panel - Problem + Code Editor (65%) */}
        <div className="flex flex-col w-2/3 border-r border-slate-700">
          {/* Problem Pane - fixed height */}
          <div className="h-44 flex-shrink-0 border-b border-slate-700 overflow-hidden">
            <ProblemPane exercise={exercise} />
          </div>

          {/* Code Editor - takes remaining space */}
          <div className="flex-1 min-h-0 bg-neutral-900">
            <CodeEditor value={code} onChange={setCode} />
          </div>

          {/* Submit Bar */}
          <div className="h-14 flex-shrink-0 flex items-center gap-3 px-3 border-t border-slate-700 bg-slate-800">
            <SubmitButton
              loading={isSubmitting}
              onClick={handleSubmit}
            />
            <ResultBadge result={result} />

            {result?.is_correct && (
              <button
                onClick={handleNextExercise}
                className="ml-auto px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm font-medium"
              >
                Next Exercise →
              </button>
            )}
          </div>
        </div>

        {/* Right Panel - Hints (35%) */}
        <div className="w-1/3 flex flex-col min-h-0">
          <HintPanel
            hints={hintSystem.hints}
            currentLevel={hintSystem.currentLevel}
            isExhausted={hintSystem.isExhausted}
            isLoading={hintSystem.isLoading}
            onRequestHint={hintSystem.requestHint}
            isSolved={result?.is_correct}
          />
        </div>
      </div>
    </div>
  );
}
