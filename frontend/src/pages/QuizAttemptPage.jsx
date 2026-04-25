import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";

import { api } from "../api/client";

export default function QuizAttemptPage() {
  const { quizId, attemptId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = localStorage.getItem("session_id");
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const savedResults = sessionStorage.getItem(`quiz_${attemptId}_results`);

    if (savedResults) {
      setSubmitted(true);
      setResults(JSON.parse(savedResults));
      return;
    }

    // Check for questions passed via navigation state
    const stateQuestions = location.state?.questions;
    if (stateQuestions && stateQuestions.length > 0) {
      setQuestions(stateQuestions);
      // Also save to sessionStorage for page refresh
      sessionStorage.setItem(`quiz_${attemptId}_questions`, JSON.stringify(stateQuestions));
      return;
    }

    // Check sessionStorage for previously saved questions
    const savedQuestions = sessionStorage.getItem(`quiz_${attemptId}_questions`);
    const savedAnswers = sessionStorage.getItem(`quiz_${attemptId}_answers`);

    if (savedQuestions) {
      setQuestions(JSON.parse(savedQuestions));
    }
    if (savedAnswers) {
      setAnswers(JSON.parse(savedAnswers));
    }
  }, [attemptId, location.state]);

  useEffect(() => {
    if (questions.length > 0) {
      sessionStorage.setItem(`quiz_${attemptId}_questions`, JSON.stringify(questions));
    }
  }, [questions, attemptId]);

  useEffect(() => {
    if (Object.keys(answers).length > 0) {
      sessionStorage.setItem(`quiz_${attemptId}_answers`, JSON.stringify(answers));
    }
  }, [answers, attemptId]);

  const handleAnswer = (questionId, answer) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      for (const [questionId, answer] of Object.entries(answers)) {
        await api.post("/quiz/answer", {
          attempt_id: parseInt(attemptId),
          question_id: parseInt(questionId),
          answer: answer,
        });
      }

      const { data } = await api.post("/quiz/submit", {
        attempt_id: parseInt(attemptId),
      });

      setSubmitted(true);
      setResults(data);
      sessionStorage.setItem(`quiz_${attemptId}_results`, JSON.stringify(data));
    } catch (err) {
      setError("Failed to submit quiz. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = () => {
    sessionStorage.removeItem(`quiz_${attemptId}_questions`);
    sessionStorage.removeItem(`quiz_${attemptId}_answers`);
    sessionStorage.removeItem(`quiz_${attemptId}_results`);
    navigate("/quiz");
  };

  const currentQuestion = questions[currentIndex];
  const allAnswered = questions.every((q) => answers[q.id] !== undefined);

  if (questions.length === 0) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p>Loading quiz...</p>
      </div>
    );
  }

  if (submitted && results) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <div className="max-w-2xl mx-auto p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold mb-2">Quiz Complete!</h1>
            <div className="inline-block px-6 py-4 bg-slate-800 rounded-lg border border-slate-700">
              <p className="text-4xl font-bold text-blue-400">
                {results.percentage.toFixed(0)}%
              </p>
              <p className="text-slate-400 mt-1">
                {results.score} / {results.max_score} points
              </p>
            </div>
          </div>

          <div className="space-y-4 mb-8">
            <h2 className="text-lg font-semibold">Question Summary</h2>
            {questions.map((q, idx) => {
              const response = results.responses.find((r) => r.question_id === q.id);
              const isCorrect = response?.is_correct;
              const correctAnswer = results.correct_answers?.[q.id];
              return (
                <div
                  key={q.id}
                  className={`p-4 rounded-lg border ${
                    isCorrect
                      ? "bg-green-900/30 border-green-700"
                      : "bg-red-900/30 border-red-700"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${
                        isCorrect ? "bg-green-600" : "bg-red-600"
                      }`}
                    >
                      {isCorrect ? "✓" : "✗"}
                    </span>
                    <div>
                      <p className="text-sm text-slate-300 mb-1">
                        Question {idx + 1}: {q.question_text}
                      </p>
                      <p className="text-sm text-slate-400">
                        Your answer: <span className="text-slate-300">{response?.answer || "Not answered"}</span>
                      </p>
                      {!isCorrect && correctAnswer && (
                        <p className="text-sm text-slate-400">
                          Correct answer: <span className="text-green-400">{correctAnswer}</span>
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={handleFinish}
            className="w-full py-3 rounded bg-blue-600 hover:bg-blue-500 font-medium transition-colors"
          >
            Back to Quizzes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">Quiz</h1>
            <p className="text-sm text-slate-400">
              Question {currentIndex + 1} of {questions.length}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-400">Progress</p>
            <div className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{
                  width: `${((currentIndex + 1) / questions.length) * 100}%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Question */}
      <div className="max-w-3xl mx-auto p-6">
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
            {error}
          </div>
        )}

        <div className="mb-8">
          <p className="text-xl mb-6">{currentQuestion.question_text}</p>

          {currentQuestion.question_type === "multiple_choice" ? (
            <div className="space-y-3">
              {currentQuestion.options?.map((option, idx) => (
                <label
                  key={idx}
                  className={`flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-colors ${
                    answers[currentQuestion.id] === option
                      ? "bg-blue-900/30 border-blue-500"
                      : "bg-slate-800 border-slate-700 hover:border-slate-600"
                  }`}
                >
                  <input
                    type="radio"
                    name={`question_${currentQuestion.id}`}
                    value={option}
                    checked={answers[currentQuestion.id] === option}
                    onChange={() => handleAnswer(currentQuestion.id, option)}
                    className="w-5 h-5 accent-blue-500"
                  />
                  <span className="text-slate-200">{option}</span>
                </label>
              ))}
            </div>
          ) : (
            <input
              type="text"
              value={answers[currentQuestion.id] || ""}
              onChange={(e) => handleAnswer(currentQuestion.id, e.target.value)}
              placeholder="Type your answer..."
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:border-blue-500 focus:outline-none"
            />
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-6 border-t border-slate-800">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className="px-6 py-2 rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>

          {currentIndex < questions.length - 1 ? (
            <button
              onClick={handleNext}
              className="px-6 py-2 rounded bg-blue-600 hover:bg-blue-500 transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading || !allAnswered}
              className="px-6 py-2 rounded bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? "Submitting..." : "Submit Quiz"}
            </button>
          )}
        </div>

        {!allAnswered && (
          <p className="mt-4 text-center text-sm text-slate-400">
            {Object.keys(answers).length} of {questions.length} questions answered
          </p>
        )}
      </div>
    </div>
  );
}
