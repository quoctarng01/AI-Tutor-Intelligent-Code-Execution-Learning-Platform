import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";

import { api } from "../api/client";

export default function SurveyResponsePage() {
  const { surveyId, responseId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = localStorage.getItem("session_id");
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [textResponses, setTextResponses] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const savedSubmitted = sessionStorage.getItem(`survey_${responseId}_submitted`);

    if (savedSubmitted === "true") {
      setSubmitted(true);
      return;
    }

    // Check for questions passed via navigation state
    const stateQuestions = location.state?.questions;
    if (stateQuestions && stateQuestions.length > 0) {
      setQuestions(stateQuestions);
      sessionStorage.setItem(`survey_${responseId}_questions`, JSON.stringify(stateQuestions));
      return;
    }

    // Check sessionStorage for previously saved questions
    const savedQuestions = sessionStorage.getItem(`survey_${responseId}_questions`);
    const savedAnswers = sessionStorage.getItem(`survey_${responseId}_answers`);
    const savedTextResponses = sessionStorage.getItem(`survey_${responseId}_text`);

    if (savedQuestions) {
      setQuestions(JSON.parse(savedQuestions));
    }
    if (savedAnswers) {
      setAnswers(JSON.parse(savedAnswers));
    }
    if (savedTextResponses) {
      setTextResponses(JSON.parse(savedTextResponses));
    }
  }, [responseId, location.state]);

  useEffect(() => {
    if (questions.length > 0) {
      sessionStorage.setItem(`survey_${responseId}_questions`, JSON.stringify(questions));
    }
  }, [questions, responseId]);

  useEffect(() => {
    if (Object.keys(answers).length > 0) {
      sessionStorage.setItem(`survey_${responseId}_answers`, JSON.stringify(answers));
    }
  }, [answers, responseId]);

  useEffect(() => {
    if (Object.keys(textResponses).length > 0) {
      sessionStorage.setItem(`survey_${responseId}_text`, JSON.stringify(textResponses));
    }
  }, [textResponses, responseId]);

  const handleLikertSelect = (questionId, value) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleTextResponse = (questionId, text) => {
    setTextResponses((prev) => ({ ...prev, [questionId]: text }));
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
      for (const [questionId, value] of Object.entries(answers)) {
        await api.post("/survey/answer", {
          response_id: parseInt(responseId),
          question_id: parseInt(questionId),
          value: value,
          text_response: textResponses[questionId] || null,
        });
      }

      await api.post("/survey/complete", {
        response_id: parseInt(responseId),
      });

      setSubmitted(true);
      sessionStorage.setItem(`survey_${responseId}_submitted`, "true");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit survey. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = () => {
    sessionStorage.removeItem(`survey_${responseId}_questions`);
    sessionStorage.removeItem(`survey_${responseId}_answers`);
    sessionStorage.removeItem(`survey_${responseId}_text`);
    sessionStorage.removeItem(`survey_${responseId}_submitted`);
    navigate("/surveys");
  };

  const currentQuestion = questions[currentIndex];
  const allAnswered = questions.every((q) => answers[q.id] !== undefined);
  const progress = (Object.keys(answers).length / questions.length) * 100;

  if (questions.length === 0) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p>Loading survey...</p>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <div className="max-w-2xl mx-auto p-8 flex flex-col items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-green-600 flex items-center justify-center mx-auto mb-6">
              <svg
                className="w-10 h-10 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold mb-2">Thank You!</h1>
            <p className="text-slate-400 mb-8">
              Your survey response has been submitted successfully.
            </p>
            <button
              onClick={handleFinish}
              className="px-8 py-3 rounded bg-blue-600 hover:bg-blue-500 font-medium transition-colors"
            >
              Back to Surveys
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-slate-400">
              Question {currentIndex + 1} of {questions.length}
            </p>
            <p className="text-sm text-slate-400">{Math.round(progress)}% complete</p>
          </div>
          <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-purple-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
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
          {currentQuestion.question_category && (
            <span className="inline-block px-3 py-1 rounded-full bg-purple-900/50 text-purple-300 text-xs mb-4">
              {currentQuestion.question_category}
            </span>
          )}
          <p className="text-xl mb-8">{currentQuestion.question_text}</p>

          {/* Likert Scale */}
          <div className="space-y-3">
            <div className="flex justify-between text-xs text-slate-500 mb-2">
              <span>{currentQuestion.scale_min_label || "Strongly Disagree"}</span>
              <span>{currentQuestion.scale_max_label || "Strongly Agree"}</span>
            </div>
            <div className="flex justify-between gap-2">
              {Array.from(
                { length: currentQuestion.scale_max - currentQuestion.scale_min + 1 },
                (_, i) => currentQuestion.scale_min + i
              ).map((value) => (
                <button
                  key={value}
                  onClick={() => handleLikertSelect(currentQuestion.id, value)}
                  className={`flex-1 py-4 px-2 rounded-lg border-2 transition-all text-center ${
                    answers[currentQuestion.id] === value
                      ? "bg-purple-600 border-purple-500 text-white"
                      : "bg-slate-800 border-slate-700 hover:border-slate-500 text-slate-300"
                  }`}
                >
                  <span className="text-2xl font-bold">{value}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Optional Text Response */}
          <div className="mt-8">
            <label className="block text-sm text-slate-400 mb-2">
              Additional comments (optional)
            </label>
            <textarea
              value={textResponses[currentQuestion.id] || ""}
              onChange={(e) => handleTextResponse(currentQuestion.id, e.target.value)}
              placeholder="Share any additional thoughts..."
              rows={3}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:border-purple-500 focus:outline-none resize-none"
            />
          </div>
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
              className="px-6 py-2 rounded bg-purple-600 hover:bg-purple-500 transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading || !allAnswered}
              className="px-6 py-2 rounded bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? "Submitting..." : "Submit Survey"}
            </button>
          )}
        </div>

        {!allAnswered && (
          <p className="mt-4 text-center text-sm text-slate-400">
            Please answer all required questions to submit
          </p>
        )}

        {/* Question Navigator */}
        <div className="mt-8 pt-6 border-t border-slate-800">
          <p className="text-sm text-slate-400 mb-3">Jump to question:</p>
          <div className="flex flex-wrap gap-2">
            {questions.map((q, idx) => (
              <button
                key={q.id}
                onClick={() => setCurrentIndex(idx)}
                className={`w-8 h-8 rounded text-sm font-medium transition-colors ${
                  idx === currentIndex
                    ? "bg-purple-600 text-white"
                    : answers[q.id]
                    ? "bg-green-900/50 text-green-400 border border-green-700"
                    : "bg-slate-800 text-slate-400 border border-slate-700"
                }`}
              >
                {idx + 1}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
