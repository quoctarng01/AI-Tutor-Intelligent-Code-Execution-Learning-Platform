from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import Quiz, QuizAttempt, QuizQuestion, QuizResponse
from backend.schemas import (
    QuizAnswerRequest,
    QuizAttemptResponse,
    QuizListResponse,
    QuizQuestionResponse,
    QuizResponse as QuizResponseSchema,
    QuizScoreResponse,
    QuizStartRequest,
    QuizStartResponse,
    QuizSubmitRequest,
)

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("", response_model=list[QuizListResponse])
async def list_quizzes(db: AsyncSession = Depends(get_db)) -> list[QuizListResponse]:
    """List all available quizzes."""
    result = await db.execute(
        select(Quiz)
        .where(Quiz.is_active == True)
        .options(selectinload(Quiz.questions))
        .order_by(Quiz.quiz_type, Quiz.id)
    )
    quizzes = result.scalars().all()
    return [
        QuizListResponse(
            id=q.id,
            title=q.title,
            description=q.description,
            quiz_type=q.quiz_type,
            topic=q.topic,
            question_count=len(q.questions),
        )
        for q in quizzes
    ]


@router.get("/{quiz_id}", response_model=QuizResponseSchema)
async def get_quiz(quiz_id: str, db: AsyncSession = Depends(get_db)) -> QuizResponseSchema:
    """Get quiz details including questions (without correct answers)."""
    result = await db.execute(
        select(Quiz)
        .where(Quiz.id == quiz_id, Quiz.is_active == True)
        .options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz_not_found")

    return QuizResponseSchema(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        quiz_type=quiz.quiz_type,
        topic=quiz.topic,
        is_active=quiz.is_active,
        questions=[
            QuizQuestionResponse(
                id=q.id,
                quiz_id=quiz.id,
                question_number=q.question_number,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                points=q.points,
            )
            for q in sorted(quiz.questions, key=lambda x: x.question_number)
        ],
    )


@router.post("/start", response_model=QuizStartResponse)
async def start_quiz(payload: QuizStartRequest, db: AsyncSession = Depends(get_db)) -> QuizStartResponse:
    """Start a new quiz attempt for the session."""
    quiz_result = await db.execute(
        select(Quiz)
        .where(Quiz.id == payload.quiz_id, Quiz.is_active == True)
        .options(selectinload(Quiz.questions))
    )
    quiz = quiz_result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz_not_found")

    attempt = QuizAttempt(
        session_id=payload.session_id,
        quiz_id=quiz.id,
        max_score=float(sum(q.points for q in quiz.questions)),
    )
    db.add(attempt)
    await db.flush()

    return QuizStartResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        questions=[
            QuizQuestionResponse(
                id=q.id,
                quiz_id=quiz.id,
                question_number=q.question_number,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                points=q.points,
            )
            for q in sorted(quiz.questions, key=lambda x: x.question_number)
        ],
        total_questions=len(quiz.questions),
        total_points=float(sum(q.points for q in quiz.questions)),
    )


@router.post("/answer", response_model=dict)
async def answer_question(payload: QuizAnswerRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Submit an answer for a quiz question."""
    attempt_result = await db.execute(
        select(QuizAttempt).where(QuizAttempt.id == payload.attempt_id)
    )
    attempt = attempt_result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="attempt_not_found")

    question_result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id == payload.question_id)
    )
    question = question_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="question_not_found")

    is_correct = _grade_answer(question.question_type, question.correct_answer, payload.answer)
    points_earned = float(question.points) if is_correct else 0.0

    existing_response = await db.execute(
        select(QuizResponse)
        .where(QuizResponse.attempt_id == payload.attempt_id, QuizResponse.question_id == payload.question_id)
    )
    existing = existing_response.scalar_one_or_none()

    if existing:
        existing.answer = payload.answer
        existing.is_correct = is_correct
        existing.points_earned = points_earned
        response = existing
    else:
        response = QuizResponse(
            attempt_id=payload.attempt_id,
            question_id=payload.question_id,
            answer=payload.answer,
            is_correct=is_correct,
            points_earned=points_earned,
        )
        db.add(response)

    await db.commit()

    return {
        "question_id": payload.question_id,
        "is_correct": is_correct,
        "points_earned": points_earned,
    }


def _grade_answer(question_type: str, correct_answer: str, given_answer: str) -> bool:
    """Grade an answer based on question type."""
    if question_type == "short_answer":
        return given_answer.strip().lower() == correct_answer.strip().lower()
    elif question_type == "multiple_choice":
        return given_answer.strip() == correct_answer.strip()
    return False


@router.post("/submit", response_model=QuizScoreResponse)
async def submit_quiz(payload: QuizSubmitRequest, db: AsyncSession = Depends(get_db)) -> QuizScoreResponse:
    """Submit a quiz and get the final score."""
    attempt_result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.id == payload.attempt_id)
        .options(selectinload(QuizAttempt.responses))
    )
    attempt = attempt_result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="attempt_not_found")

    if attempt.is_completed:
        raise HTTPException(status_code=400, detail="quiz_already_submitted")

    # Fetch correct answers for the quiz
    questions_result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.quiz_id == attempt.quiz_id)
    )
    questions = questions_result.scalars().all()
    correct_answers = {q.id: q.correct_answer for q in questions}

    total_score = sum(r.points_earned or 0 for r in attempt.responses)
    attempt.score = total_score
    attempt.is_completed = True
    attempt.completed_at = datetime.utcnow()

    await db.commit()

    return QuizScoreResponse(
        attempt_id=attempt.id,
        score=total_score,
        max_score=attempt.max_score,
        percentage=(total_score / attempt.max_score * 100) if attempt.max_score > 0 else 0,
        is_completed=True,
        responses=[
            {
                "question_id": r.question_id,
                "answer": r.answer,
                "is_correct": r.is_correct,
                "points_earned": r.points_earned,
            }
            for r in attempt.responses
        ],
        correct_answers=correct_answers,
    )


@router.get("/attempts/{session_id}", response_model=list[QuizAttemptResponse])
async def get_session_quiz_attempts(session_id: str, db: AsyncSession = Depends(get_db)) -> list[QuizAttemptResponse]:
    """Get all quiz attempts for a session."""
    result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.session_id == session_id)
        .order_by(QuizAttempt.started_at.desc())
    )
    attempts = result.scalars().all()
    return [QuizAttemptResponse.model_validate(a) for a in attempts]


@router.get("/attempts/{session_id}/{quiz_id}", response_model=list[QuizAttemptResponse])
async def get_quiz_attempts_for_session(
    session_id: str, quiz_id: str, db: AsyncSession = Depends(get_db)
) -> list[QuizAttemptResponse]:
    """Get all attempts for a specific quiz in a session."""
    result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.session_id == session_id, QuizAttempt.quiz_id == quiz_id)
        .order_by(QuizAttempt.started_at.desc())
    )
    attempts = result.scalars().all()
    return [QuizAttemptResponse.model_validate(a) for a in attempts]
