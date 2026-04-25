/**
 * Core API type definitions for the AI Tutor frontend.
 * Defines interfaces for sessions, exercises, hints, submissions, quizzes, and surveys.
 */

/**
 * Standardized error response structure from the API.
 */
export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}

/**
 * Standardized success response wrapper.
 * @template T - The type of the data payload
 */
export interface ApiSuccess<T> {
  success: true;
  data: T;
}

/**
 * Represents an active student session.
 */
export interface Session {
  id: string;
  username: string;
  group_type: 'tutor' | 'control' | null;
  started_at: string;
}

/**
 * Request payload for starting a new session.
 */
export interface SessionStartRequest {
  username: string;
  group_type: 'tutor' | 'control';
}

/**
 * JWT token pair returned after session authentication.
 */
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * Core exercise data structure returned from the API.
 */
export interface Exercise {
  id: string;
  topic: string;
  subtopic: string | null;
  title: string;
  difficulty: number | null;
  problem_statement: string;
  concept: string;
}

/**
 * Extended exercise data including hint content and evaluation criteria.
 */
export interface ExerciseWithHints extends Exercise {
  hint_l1: string;
  hint_l2: string;
  llm_context: string;
  correct_criteria: CorrectCriteria;
  prerequisite_ids: string[];
  common_mistakes: string[];
  tags: string[];
}

/**
 * Criteria for evaluating exercise correctness.
 * Supports three evaluation modes: code execution, LLM judge, or exact match.
 */
export interface CorrectCriteria {
  type: 'code_execution' | 'llm_judge' | 'exact_match';
  test_cases?: TestCase[];
  rubric?: {
    must_contain: string[];
  };
  expected?: string;
}

/**
 * Individual test case for code execution evaluation.
 */
export interface TestCase {
  input: string;
  expected_output: string;
}

/**
 * Request payload for requesting a hint.
 */
export interface HintRequest {
  session_id: string;
  exercise_id: string;
}

/**
 * Response from the hint endpoint.
 */
export interface HintResponse {
  level: number;
  hint: string;
  is_final: boolean;
}

/**
 * Current state of the hint system for an exercise.
 */
export interface HintState {
  current_level: number;
  is_solved: boolean;
  is_exhausted: boolean;
  max_level: number;
}

/**
 * Request payload for submitting code for evaluation.
 */
export interface SubmitRequest {
  session_id: string;
  exercise_id: string;
  code: string;
  language_id: number;
  elapsed_seconds: number | null;
}

/**
 * Response from the submission endpoint.
 */
export interface SubmitResponse {
  is_correct: boolean;
  hints_used: number;
}

/**
 * Quiz metadata returned in quiz listings.
 */
export interface Quiz {
  id: string;
  title: string;
  description: string | null;
  quiz_type: 'pre' | 'post';
  topic: string | null;
  is_active: boolean;
  question_count?: number;
}

/**
 * Individual quiz question.
 */
export interface QuizQuestion {
  id: number;
  quiz_id: string;
  question_number: number;
  question_text: string;
  question_type: 'multiple_choice' | 'short_answer';
  options: string[] | null;
  explanation: string | null;
  points: number;
}

/**
 * Response when starting a quiz attempt.
 */
export interface QuizStartResponse {
  attempt_id: number;
  quiz_id: string;
  questions: QuizQuestion[];
  total_questions: number;
  total_points: number;
}

/**
 * Request payload for submitting a quiz answer.
 */
export interface QuizAnswerRequest {
  attempt_id: number;
  question_id: number;
  answer: string;
}

/**
 * Final score response after quiz completion.
 */
export interface QuizScoreResponse {
  attempt_id: number;
  score: number;
  max_score: number;
  percentage: number;
  is_completed: boolean;
  responses: QuizResponseDetail[];
}

/**
 * Individual question response within a quiz score.
 */
export interface QuizResponseDetail {
  question_id: number;
  answer: string;
  is_correct: boolean | null;
  points_earned: number;
}

/**
 * Survey metadata returned in survey listings.
 */
export interface Survey {
  id: string;
  title: string;
  description: string | null;
  survey_type: string;
  topic: string | null;
  is_active: boolean;
  question_count?: number;
}

/**
 * Individual survey question with Likert scale configuration.
 */
export interface SurveyQuestion {
  id: number;
  survey_id: string;
  question_number: number;
  question_text: string;
  question_category: string | null;
  scale_min: number;
  scale_max: number;
  scale_min_label: string | null;
  scale_max_label: string | null;
  is_required: boolean;
}

/**
 * Response when starting a survey.
 */
export interface SurveyStartResponse {
  response_id: number;
  survey_id: string;
  questions: SurveyQuestion[];
  total_questions: number;
}

/**
 * Request payload for submitting a survey answer.
 */
export interface SurveyAnswerRequest {
  response_id: number;
  question_id: number;
  value: number;
  text_response?: string;
}

/**
 * Return type for the useExercise hook.
 */
export interface UseExerciseReturn {
  exercise: Exercise | null;
  loading: boolean;
  error: string | null;
  elapsedSeconds: number;
}

/**
 * Return type for the useHintSystem hook.
 */
export interface UseHintSystemReturn {
  hints: Hint[];
  currentLevel: number;
  isExhausted: boolean;
  isLoading: boolean;
  error: string | null;
  requestHint: () => Promise<void>;
}

/**
 * Individual hint with its level and text content.
 */
export interface Hint {
  level: number;
  text: string;
}

/**
 * Return type for the useSubmit hook.
 */
export interface UseSubmitReturn {
  submit: (
    sourceCode: string,
    currentHintLevel: number,
    elapsedSeconds?: number | null
  ) => Promise<SubmitResponse | null>;
  result: SubmitResponse | null;
  code: string;
  setCode: (code: string) => void;
  isSubmitting: boolean;
  error: string | null;
}
