import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";
import { TopBar } from "../components/layout/TopBar";

export default function QuizPage() {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const sessionId = localStorage.getItem("session_id");
  const username = localStorage.getItem("username");

  useEffect(() => {
    if (!sessionId) {
      navigate("/login");
      return;
    }
    loadQuizzes();
  }, [sessionId, navigate]);

  const loadQuizzes = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get("/quiz");
      setQuizzes(data);
    } catch (err) {
      setError("Failed to load quizzes");
    } finally {
      setLoading(false);
    }
  };

  const startQuiz = async (quizId, quizType) => {
    try {
      const { data } = await api.post("/quiz/start", {
        session_id: sessionId,
        quiz_id: quizId,
      });
      navigate(`/quiz/${quizId}/attempt/${data.attempt_id}`, {
        state: { questions: data.questions, totalQuestions: data.total_questions, quizType },
      });
    } catch (err) {
      setError("Failed to start quiz");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p>Loading quizzes...</p>
      </div>
    );
  }

  const preQuizzes = quizzes.filter((q) => q.quiz_type === "pre");
  const postQuizzes = quizzes.filter((q) => q.quiz_type === "post");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <TopBar username={username} />

      <div className="max-w-4xl mx-auto p-8">
        <h1 className="text-2xl font-bold mb-6">Assessment Quizzes</h1>

        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {/* Pre-Assessment Section */}
        <section className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold">
              1
            </div>
            <h2 className="text-xl font-semibold text-blue-400">Pre-Assessment</h2>
          </div>
          <p className="text-slate-400 mb-4">
            Take this quiz before starting the exercises to measure your current knowledge.
          </p>

          {preQuizzes.length === 0 ? (
            <p className="text-slate-500 italic">No pre-assessment quizzes available.</p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {preQuizzes.map((quiz) => (
                <QuizCard
                  key={quiz.id}
                  quiz={quiz}
                  onStart={() => startQuiz(quiz.id, quiz.quiz_type)}
                  badgeColor="bg-blue-600"
                />
              ))}
            </div>
          )}
        </section>

        {/* Post-Assessment Section */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-sm font-bold">
              2
            </div>
            <h2 className="text-xl font-semibold text-green-400">Post-Assessment</h2>
          </div>
          <p className="text-slate-400 mb-4">
            Take this quiz after completing the exercises to measure your learning progress.
          </p>

          {postQuizzes.length === 0 ? (
            <p className="text-slate-500 italic">No post-assessment quizzes available.</p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {postQuizzes.map((quiz) => (
                <QuizCard
                  key={quiz.id}
                  quiz={quiz}
                  onStart={() => startQuiz(quiz.id, quiz.quiz_type)}
                  badgeColor="bg-green-600"
                />
              ))}
            </div>
          )}
        </section>

        <div className="mt-8 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">
            <span className="font-semibold text-slate-300">Note:</span> Pre and post assessments
            help measure your learning progress. Your scores are recorded but do not affect your
            exercise completion.
          </p>
        </div>
      </div>
    </div>
  );
}

function QuizCard({ quiz, onStart, badgeColor }) {
  return (
    <div className="p-5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <span className={`px-2 py-1 rounded text-xs font-medium ${badgeColor} text-white`}>
          {quiz.quiz_type.toUpperCase()}
        </span>
        <span className="text-sm text-slate-400">{quiz.question_count} questions</span>
      </div>
      <h3 className="font-semibold text-lg mb-2">{quiz.title}</h3>
      {quiz.description && (
        <p className="text-sm text-slate-400 mb-4">{quiz.description}</p>
      )}
      {quiz.topic && (
        <p className="text-xs text-slate-500 mb-4">Topic: {quiz.topic}</p>
      )}
      <button
        onClick={onStart}
        className="w-full py-2 rounded bg-blue-600 hover:bg-blue-500 font-medium transition-colors"
      >
        Start Quiz
      </button>
    </div>
  );
}
