"""
SQLAlchemy ORM models for the AI Tutor application.
Defines database schema for exercises, sessions, attempts, hints, quizzes, and surveys.
"""

import uuid
from datetime import datetime

from sqlalchemy import BIGINT, JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Exercise(Base):
    """
    Python programming exercise with hints and test cases.
    
    Attributes:
        id: Unique exercise identifier (e.g., 'loop_001')
        topic: Broad category (e.g., 'loops', 'conditionals')
        subtopic: Fine-grained topic
        title: Human-readable title
        difficulty: Difficulty rating 1-5
        problem_statement: Full problem description
        hint_l1: Pre-authored level 1 hint (concept reminder)
        hint_l2: Pre-authored level 2 hint (reasoning guidance)
        llm_context: Context for LLM-generated hints (L3/L4)
        concept: Core programming concept
        correct_criteria: JSONB with evaluation config
        prerequisite_ids: List of exercise IDs that should be completed first
        common_mistakes: List of common error patterns
        tags: Searchable tags for filtering
    """
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    topic: Mapped[str] = mapped_column(String(50), nullable=False)
    subtopic: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[int | None] = mapped_column(SmallInteger)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    hint_l1: Mapped[str] = mapped_column(Text, nullable=False)
    hint_l2: Mapped[str] = mapped_column(Text, nullable=False)
    llm_context: Mapped[str] = mapped_column(Text, nullable=False)
    concept: Mapped[str] = mapped_column(String(200), nullable=False)
    correct_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False)
    prerequisite_ids: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    common_mistakes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    __table_args__ = (CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_exercises_difficulty_range"),)


class Session(Base):
    """
    Student learning session.
    
    Attributes:
        id: Unique session UUID (auto-generated)
        username: Student's display name
        group_type: 'tutor' or 'control' for A/B testing
        started_at: Session start timestamp
        ended_at: Session end timestamp (null if active)
    """
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    group_type: Mapped[str | None] = mapped_column(String(10))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    attempts: Mapped[list["Attempt"]] = relationship(back_populates="session")
    hint_logs: Mapped[list["HintLog"]] = relationship(back_populates="session")
    hint_states: Mapped[list["HintState"]] = relationship(back_populates="session")

    __table_args__ = (
        CheckConstraint("group_type IN ('tutor','control')", name="ck_sessions_group_type"),
    )


class Attempt(Base):
    """
    Code submission attempt record.
    
    Attributes:
        id: Unique attempt ID
        session_id: Reference to student session
        exercise_id: Reference to exercise
        submitted_code: The code that was submitted
        is_correct: Whether the submission was correct
        hints_used: Number of hints used at time of submission
        time_to_solve_s: Time spent on exercise in seconds
        hint_state: Hint state string (e.g., 'HINT_2' or 'IDLE')
        submitted_at: Timestamp of submission
    """
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    exercise_id: Mapped[str] = mapped_column(String(20), ForeignKey("exercises.id"))
    submitted_code: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    hints_used: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    time_to_solve_s: Mapped[int | None] = mapped_column(Integer)
    hint_state: Mapped[str] = mapped_column(String(20), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    session: Mapped["Session"] = relationship(back_populates="attempts")


class HintState(Base):
    """
    Authoritative hint state machine per session-exercise combination.
    
    This is the single source of truth for hint progression.
    Never compute hint level from hint_logs to prevent manipulation.
    
    Attributes:
        session_id: Part of composite primary key
        exercise_id: Part of composite primary key
        current_level: Current hint level (0-4)
        is_solved: Whether the exercise has been solved
        opened_at: When hints were first requested
    """
    __tablename__ = "hint_state"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), primary_key=True)
    exercise_id: Mapped[str] = mapped_column(String(20), ForeignKey("exercises.id"), primary_key=True)
    current_level: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    is_solved: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    session: Mapped["Session"] = relationship(back_populates="hint_states")


class HintLog(Base):
    """
    Audit log of all hint deliveries.
    
    Records every hint that was requested and delivered, including
    the full prompt sent to the LLM and the response received.
    Used for research analysis and rubric scoring.
    
    Attributes:
        id: Unique log entry ID
        session_id: Reference to student session
        exercise_id: Reference to exercise
        hint_level: Level of hint delivered (1-4)
        prompt_version: Version of the prompt template used
        prompt_rendered: Full prompt sent to LLM (for LLM hints)
        llm_response: The hint text delivered
        was_pre_authored: Whether hint was pre-authored (L1/L2) or LLM (L3/L4)
        delivered_at: Timestamp of delivery
    """
    __tablename__ = "hint_logs"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    exercise_id: Mapped[str] = mapped_column(String(20), ForeignKey("exercises.id"))
    hint_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt_rendered: Mapped[str] = mapped_column(Text, nullable=False)
    llm_response: Mapped[str] = mapped_column(Text, nullable=False)
    was_pre_authored: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    session: Mapped["Session"] = relationship(back_populates="hint_logs")


# ============================================================
# Pre/Post Assessment Quiz Models
# ============================================================

class Quiz(Base):
    """
    A quiz containing questions for pre/post assessment.
    
    Attributes:
        id: Unique quiz identifier
        title: Human-readable quiz title
        description: Quiz description
        quiz_type: 'pre' (pre-assessment) or 'post' (post-assessment)
        topic: Optional topic association
        is_active: Whether quiz is available
        created_at: Creation timestamp
    """
    __tablename__ = "quizzes"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    quiz_type: Mapped[str] = mapped_column(String(20), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (
        CheckConstraint("quiz_type IN ('pre','post')", name="ck_quizzes_quiz_type"),
    )

    questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    """
    Individual question within a quiz.
    
    Attributes:
        id: Unique question ID
        quiz_id: Reference to parent quiz
        question_number: Order within quiz
        question_text: The question text
        question_type: 'multiple_choice' or 'short_answer'
        options: List of options (for multiple choice)
        correct_answer: The correct answer
        explanation: Explanation shown after submission
        points: Point value for this question
    """
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    quiz_id: Mapped[str] = mapped_column(String(30), ForeignKey("quizzes.id", ondelete="CASCADE"))
    question_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    points: Mapped[int] = mapped_column(SmallInteger, server_default=text("1"))

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")

    __table_args__ = (
        CheckConstraint("question_type IN ('multiple_choice','short_answer')", name="ck_quiz_questions_type"),
        CheckConstraint("points >= 0", name="ck_quiz_questions_points"),
    )

    responses: Mapped[list["QuizResponse"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class QuizAttempt(Base):
    """
    A student's attempt at a quiz.
    
    Attributes:
        id: Unique attempt ID
        session_id: Reference to student session
        quiz_id: Reference to quiz
        score: Points earned
        max_score: Maximum possible points
        is_completed: Whether the attempt is finished
        started_at: When the attempt began
        completed_at: When the attempt was submitted
    """
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    quiz_id: Mapped[str] = mapped_column(String(30), ForeignKey("quizzes.id", ondelete="CASCADE"))
    score: Mapped[float] = mapped_column(server_default=text("0"))
    max_score: Mapped[float] = mapped_column(server_default=text("0"))
    is_completed: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped["Session"] = relationship()
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
    responses: Mapped[list["QuizResponse"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")


class QuizResponse(Base):
    """
    Individual response to a quiz question.
    
    Attributes:
        id: Unique response ID
        attempt_id: Reference to quiz attempt
        question_id: Reference to question
        answer: The student's answer
        is_correct: Whether the answer is correct (null until graded)
        points_earned: Points earned for this response
        answered_at: When the answer was submitted
    """
    __tablename__ = "quiz_responses"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("quiz_attempts.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("quiz_questions.id", ondelete="CASCADE"))
    answer: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    points_earned: Mapped[float] = mapped_column(server_default=text("0"))
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    attempt: Mapped["QuizAttempt"] = relationship(back_populates="responses")
    question: Mapped["QuizQuestion"] = relationship(back_populates="responses")


# ============================================================
# Likert Scale Survey Models
# ============================================================

class Survey(Base):
    """
    A Likert-scale survey for collecting feedback.
    
    Attributes:
        id: Unique survey identifier
        title: Human-readable survey title
        description: Survey description
        survey_type: 'likert', 'feedback', or 'diagnostic'
        topic: Optional topic association
        is_active: Whether survey is available
        created_at: Creation timestamp
    """
    __tablename__ = "surveys"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    survey_type: Mapped[str] = mapped_column(String(50), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    questions: Mapped[list["SurveyQuestion"]] = relationship(back_populates="survey", cascade="all, delete-orphan")
    responses: Mapped[list["SurveyResponse"]] = relationship(back_populates="survey", cascade="all, delete-orphan")


class SurveyQuestion(Base):
    """
    Individual Likert-scale question.
    
    Attributes:
        id: Unique question ID
        survey_id: Reference to parent survey
        question_number: Order within survey
        question_text: The question text
        question_category: 'engagement', 'difficulty', 'confidence', etc.
        scale_min: Minimum scale value (usually 1)
        scale_max: Maximum scale value (usually 5)
        scale_min_label: Label for minimum (e.g., "Strongly Disagree")
        scale_max_label: Label for maximum (e.g., "Strongly Agree")
        is_required: Whether question must be answered
    """
    __tablename__ = "survey_questions"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    survey_id: Mapped[str] = mapped_column(String(30), ForeignKey("surveys.id", ondelete="CASCADE"))
    question_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[str | None] = mapped_column(String(50))
    scale_min: Mapped[int] = mapped_column(SmallInteger, server_default=text("1"))
    scale_max: Mapped[int] = mapped_column(SmallInteger, server_default=text("5"))
    scale_min_label: Mapped[str | None] = mapped_column(String(100))
    scale_max_label: Mapped[str | None] = mapped_column(String(100))
    is_required: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))

    survey: Mapped["Survey"] = relationship(back_populates="questions")
    answers: Mapped[list["SurveyAnswer"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class SurveyResponse(Base):
    """
    A student's response session to a survey.
    
    Attributes:
        id: Unique response session ID
        session_id: Reference to student session
        survey_id: Reference to survey
        is_complete: Whether the survey has been submitted
        started_at: When the survey was started
        completed_at: When the survey was submitted
    """
    __tablename__ = "survey_responses"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    survey_id: Mapped[str] = mapped_column(String(30), ForeignKey("surveys.id", ondelete="CASCADE"))
    is_complete: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped["Session"] = relationship()
    survey: Mapped["Survey"] = relationship(back_populates="responses")
    answers: Mapped[list["SurveyAnswer"]] = relationship(back_populates="response", cascade="all, delete-orphan")


class SurveyAnswer(Base):
    """
    Individual Likert scale answer to a survey question.
    
    Attributes:
        id: Unique answer ID
        response_id: Reference to survey response session
        question_id: Reference to question
        value: Likert scale value (e.g., 1-5)
        text_response: Optional free-text response
        answered_at: When the answer was submitted
    """
    __tablename__ = "survey_answers"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    response_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("survey_responses.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("survey_questions.id", ondelete="CASCADE"))
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    text_response: Mapped[str | None] = mapped_column(Text)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    response: Mapped["SurveyResponse"] = relationship(back_populates="answers")
    question: Mapped["SurveyQuestion"] = relationship(back_populates="answers")
