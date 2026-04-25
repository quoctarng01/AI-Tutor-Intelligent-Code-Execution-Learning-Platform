import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";
import { TopBar } from "../components/layout/TopBar";

export default function SurveyPage() {
  const [surveys, setSurveys] = useState([]);
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
    loadSurveys();
  }, [sessionId, navigate]);

  const loadSurveys = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get("/survey");
      setSurveys(data);
    } catch (err) {
      setError("Failed to load surveys");
    } finally {
      setLoading(false);
    }
  };

  const startSurvey = async (surveyId) => {
    try {
      const { data } = await api.post("/survey/start", {
        session_id: sessionId,
        survey_id: surveyId,
      });
      navigate(`/survey/${surveyId}/response/${data.response_id}`, {
        state: { questions: data.questions, totalQuestions: data.total_questions },
      });
    } catch (err) {
      setError("Failed to start survey");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p>Loading surveys...</p>
      </div>
    );
  }

  const likertSurveys = surveys.filter((s) => s.survey_type === "likert");
  const feedbackSurveys = surveys.filter((s) => s.survey_type === "feedback");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <TopBar username={username} />

      <div className="max-w-4xl mx-auto p-8">
        <h1 className="text-2xl font-bold mb-2">Surveys</h1>
        <p className="text-slate-400 mb-8">
          Help us improve by sharing your feedback. Your responses are anonymous.
        </p>

        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {/* Likert Scale Surveys */}
        <section className="mb-10">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="text-purple-400">Likert Scale Surveys</span>
          </h2>
          <p className="text-slate-400 mb-4">
            Rate your agreement with statements using a 1-5 scale.
          </p>

          {likertSurveys.length === 0 ? (
            <p className="text-slate-500 italic">No Likert surveys available.</p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {likertSurveys.map((survey) => (
                <SurveyCard
                  key={survey.id}
                  survey={survey}
                  onStart={() => startSurvey(survey.id)}
                  badgeColor="bg-purple-600"
                />
              ))}
            </div>
          )}
        </section>

        {/* Feedback Surveys */}
        <section>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="text-amber-400">Feedback Surveys</span>
          </h2>
          <p className="text-slate-400 mb-4">
            Share your thoughts and suggestions to help us improve.
          </p>

          {feedbackSurveys.length === 0 ? (
            <p className="text-slate-500 italic">No feedback surveys available.</p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {feedbackSurveys.map((survey) => (
                <SurveyCard
                  key={survey.id}
                  survey={survey}
                  onStart={() => startSurvey(survey.id)}
                  badgeColor="bg-amber-600"
                />
              ))}
            </div>
          )}
        </section>

        <div className="mt-8 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
          <p className="text-sm text-slate-400">
            <span className="font-semibold text-slate-300">Likert Scale:</span> 1 = Strongly
            Disagree, 2 = Disagree, 3 = Neutral, 4 = Agree, 5 = Strongly Agree
          </p>
        </div>
      </div>
    </div>
  );
}

function SurveyCard({ survey, onStart, badgeColor }) {
  return (
    <div className="p-5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <span className={`px-2 py-1 rounded text-xs font-medium ${badgeColor} text-white`}>
          {survey.survey_type.toUpperCase()}
        </span>
        <span className="text-sm text-slate-400">{survey.question_count} questions</span>
      </div>
      <h3 className="font-semibold text-lg mb-2">{survey.title}</h3>
      {survey.description && <p className="text-sm text-slate-400 mb-4">{survey.description}</p>}
      {survey.topic && <p className="text-xs text-slate-500 mb-4">Topic: {survey.topic}</p>}
      <button
        onClick={onStart}
        className="w-full py-2 rounded bg-purple-600 hover:bg-purple-500 font-medium transition-colors"
      >
        Take Survey
      </button>
    </div>
  );
}
