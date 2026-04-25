from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class SessionStartRequest(BaseModel):
    username: str = Field(..., min_length=1)
    group_type: str = Field(..., pattern="^(tutor|control)$")


class SessionResponse(BaseModel):
    id: UUID
    username: str
    group_type: str | None = None
    started_at: datetime
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None

    model_config = {"from_attributes": True}


class ExerciseResponse(BaseModel):
    id: str
    topic: str
    subtopic: str | None = None
    title: str
    difficulty: int | None = None
    problem_statement: str
    concept: str

    model_config = {"from_attributes": True}


class HintRequest(BaseModel):
    session_id: UUID
    exercise_id: str


class HintResponse(BaseModel):
    level: int
    hint: str
    is_final: bool


class SubmitRequest(BaseModel):
    session_id: UUID
    exercise_id: str
    code: str
    language_id: int = 71
    elapsed_seconds: int | None = None


class SubmitResponse(BaseModel):
    is_correct: bool
    hints_used: int


# ============================================================
# Quiz Schemas (Pre/Post Assessment)
# ============================================================

class QuizQuestionBase(BaseModel):
    question_number: int
    question_text: str
    question_type: str = Field(..., pattern="^(multiple_choice|short_answer)$")
    options: list[str] | None = None
    points: int = 1


class QuizQuestionResponse(QuizQuestionBase):
    id: int
    quiz_id: str
    explanation: str | None = None

    model_config = {"from_attributes": True}


class QuizQuestionWithAnswer(QuizQuestionResponse):
    correct_answer: str


class QuizResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    quiz_type: str
    topic: str | None = None
    is_active: bool
    questions: list[QuizQuestionResponse]

    model_config = {"from_attributes": True}


class QuizListResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    quiz_type: str
    topic: str | None = None
    question_count: int

    model_config = {"from_attributes": True}


class QuizStartRequest(BaseModel):
    quiz_id: str
    session_id: str


class QuizStartResponse(BaseModel):
    attempt_id: int
    quiz_id: str
    questions: list[QuizQuestionResponse]
    total_questions: int
    total_points: float


class QuizAnswerRequest(BaseModel):
    attempt_id: int
    question_id: int
    answer: str


class QuizSubmitRequest(BaseModel):
    attempt_id: int


class QuizScoreResponse(BaseModel):
    attempt_id: int
    score: float
    max_score: float
    percentage: float
    is_completed: bool
    responses: list[dict]
    correct_answers: dict[int, str] = {}


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: str
    score: float
    max_score: float
    is_completed: bool
    started_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


# ============================================================
# Survey Schemas (Likert Scale)
# ============================================================

class SurveyQuestionBase(BaseModel):
    question_number: int
    question_text: str
    question_category: str | None = None
    scale_min: int = 1
    scale_max: int = 5
    scale_min_label: str | None = None
    scale_max_label: str | None = None
    is_required: bool = True


class SurveyQuestionResponse(SurveyQuestionBase):
    id: int
    survey_id: str

    model_config = {"from_attributes": True}


class SurveyResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    survey_type: str
    topic: str | None = None
    is_active: bool
    questions: list[SurveyQuestionResponse]

    model_config = {"from_attributes": True}


class SurveyListResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    survey_type: str
    topic: str | None = None
    question_count: int

    model_config = {"from_attributes": True}


class SurveyStartRequest(BaseModel):
    survey_id: str
    session_id: str


class SurveyStartResponse(BaseModel):
    response_id: int
    survey_id: str
    questions: list[SurveyQuestionResponse]
    total_questions: int


class SurveyAnswerRequest(BaseModel):
    response_id: int
    question_id: int
    value: int = Field(..., ge=1, le=5)
    text_response: str | None = None


class SurveyCompleteRequest(BaseModel):
    response_id: int


class SurveyCompleteResponse(BaseModel):
    response_id: int
    is_complete: bool
    questions_answered: int
    completed_at: datetime | None = None


class SurveyStatsResponse(BaseModel):
    survey_id: str
    total_responses: int
    average_by_question: dict[int, float]
    category_averages: dict[str, float]
