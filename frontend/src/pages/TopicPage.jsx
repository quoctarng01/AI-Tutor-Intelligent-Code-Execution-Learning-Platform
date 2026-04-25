import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";

export default function TopicPage() {
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get("/exercises")
      .then(({ data }) => setExercises(data))
      .finally(() => setLoading(false));
  }, []);

  const topics = useMemo(() => {
    const grouped = new Map();
    exercises.forEach((item) => {
      if (!grouped.has(item.topic)) grouped.set(item.topic, []);
      grouped.get(item.topic).push(item);
    });
    return [...grouped.entries()];
  }, [exercises]);

  if (loading) return <div className="p-8 text-slate-200">Loading topics...</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Navigation Bar */}
      <nav className="border-b border-slate-800 bg-slate-900/50">
        <div className="max-w-4xl mx-auto px-8 py-4 flex items-center gap-8">
          <h1 className="text-xl font-semibold">AI Tutor</h1>
          <div className="flex items-center gap-6">
            <button
              onClick={() => navigate("/topics")}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              Exercises
            </button>
            <button
              onClick={() => navigate("/quiz")}
              className="text-sm text-green-400 hover:text-green-300"
            >
              Quiz
            </button>
            <button
              onClick={() => navigate("/surveys")}
              className="text-sm text-purple-400 hover:text-purple-300"
            >
              Surveys
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto p-8">
        <h2 className="text-2xl font-semibold mb-2">Practice Exercises</h2>
        <p className="text-slate-400 mb-8">
          Choose a topic to practice Python programming fundamentals. Each topic contains exercises
          with increasing difficulty.
        </p>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {topics.map(([topic, list]) => (
            <button
              key={topic}
              onClick={() => navigate(`/exercise/${list[0].id}`)}
              className="text-left p-5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 hover:border-slate-600 transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold capitalize">{topic}</h3>
                <span className="text-xs text-slate-500">{list.length} exercises</span>
              </div>
              <p className="text-sm text-slate-400">
                {topic === "loops" && "Master for and while loops"}
                {topic === "conditionals" && "Learn if, elif, and else"}
                {topic === "variables" && "Work with variables and data"}
                {topic === "functions" && "Create reusable functions"}
                {topic === "lists" && "Handle collections of data"}
                {topic === "strings" && "Manipulate text data"}
              </p>
              <div className="mt-3 flex gap-1">
                {Array.from({ length: Math.max(...list.map((e) => e.difficulty || 1)) }).map(
                  (_, i) => (
                    <span
                      key={i}
                      className="w-2 h-2 rounded-full bg-blue-500"
                    />
                  )
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Assessment Cards */}
        <div className="mt-12">
          <h2 className="text-xl font-semibold mb-4">Assessments</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <button
              onClick={() => navigate("/quiz")}
              className="text-left p-5 rounded-lg border border-green-700 bg-green-900/20 hover:bg-green-900/30 transition-all"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-full bg-green-600 flex items-center justify-center">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                </div>
                <h3 className="font-semibold text-green-400">Pre/Post Quiz</h3>
              </div>
              <p className="text-sm text-slate-400">
                Test your knowledge before and after the exercises. Track your learning progress.
              </p>
            </button>

            <button
              onClick={() => navigate("/surveys")}
              className="text-left p-5 rounded-lg border border-purple-700 bg-purple-900/20 hover:bg-purple-900/30 transition-all"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-purple-400">Feedback Surveys</h3>
              </div>
              <p className="text-sm text-slate-400">
                Share your experience and help us improve the learning platform.
              </p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
