import { Navigate, Route, Routes } from "react-router-dom";

import ExercisePage from "./pages/ExercisePage";
import LoginPage from "./pages/LoginPage";
import QuizAttemptPage from "./pages/QuizAttemptPage";
import QuizPage from "./pages/QuizPage";
import SurveyPage from "./pages/SurveyPage";
import SurveyResponsePage from "./pages/SurveyResponsePage";
import TopicPage from "./pages/TopicPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/topics" element={<TopicPage />} />
      <Route path="/exercise/:exerciseId" element={<ExercisePage />} />
      <Route path="/quiz" element={<QuizPage />} />
      <Route path="/quiz/:quizId/attempt/:attemptId" element={<QuizAttemptPage />} />
      <Route path="/surveys" element={<SurveyPage />} />
      <Route path="/survey/:surveyId/response/:responseId" element={<SurveyResponsePage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
