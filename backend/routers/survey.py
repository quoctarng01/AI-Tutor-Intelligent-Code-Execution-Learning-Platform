from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import Survey, SurveyAnswer, SurveyQuestion, SurveyResponse
from backend.schemas import (
    SurveyAnswerRequest,
    SurveyCompleteRequest,
    SurveyCompleteResponse,
    SurveyListResponse,
    SurveyQuestionResponse,
    SurveyResponse as SurveyResponseSchema,
    SurveyStartRequest,
    SurveyStartResponse,
    SurveyStatsResponse,
)

router = APIRouter(prefix="/survey", tags=["survey"])


@router.get("", response_model=list[SurveyListResponse])
async def list_surveys(db: AsyncSession = Depends(get_db)) -> list[SurveyListResponse]:
    """List all available surveys."""
    result = await db.execute(
        select(Survey)
        .where(Survey.is_active == True)
        .options(selectinload(Survey.questions))
        .order_by(Survey.survey_type, Survey.id)
    )
    surveys = result.scalars().all()
    return [
        SurveyListResponse(
            id=s.id,
            title=s.title,
            description=s.description,
            survey_type=s.survey_type,
            topic=s.topic,
            question_count=len(s.questions),
        )
        for s in surveys
    ]


@router.get("/{survey_id}", response_model=SurveyResponseSchema)
async def get_survey(survey_id: str, db: AsyncSession = Depends(get_db)) -> SurveyResponseSchema:
    """Get survey details including questions."""
    result = await db.execute(
        select(Survey)
        .where(Survey.id == survey_id, Survey.is_active == True)
        .options(selectinload(Survey.questions))
    )
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="survey_not_found")

    return SurveyResponseSchema(
        id=survey.id,
        title=survey.title,
        description=survey.description,
        survey_type=survey.survey_type,
        topic=survey.topic,
        is_active=survey.is_active,
        questions=[
            SurveyQuestionResponse(
                id=q.id,
                survey_id=survey.id,
                question_number=q.question_number,
                question_text=q.question_text,
                question_category=q.question_category,
                scale_min=q.scale_min,
                scale_max=q.scale_max,
                scale_min_label=q.scale_min_label,
                scale_max_label=q.scale_max_label,
                is_required=q.is_required,
            )
            for q in sorted(survey.questions, key=lambda x: x.question_number)
        ],
    )


@router.post("/start", response_model=SurveyStartResponse)
async def start_survey(payload: SurveyStartRequest, db: AsyncSession = Depends(get_db)) -> SurveyStartResponse:
    """Start a new survey response for the session."""
    survey_result = await db.execute(
        select(Survey)
        .where(Survey.id == payload.survey_id, Survey.is_active == True)
        .options(selectinload(Survey.questions))
    )
    survey = survey_result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="survey_not_found")

    response = SurveyResponse(
        session_id=payload.session_id,
        survey_id=survey.id,
    )
    db.add(response)
    await db.flush()

    return SurveyStartResponse(
        response_id=response.id,
        survey_id=survey.id,
        questions=[
            SurveyQuestionResponse(
                id=q.id,
                survey_id=survey.id,
                question_number=q.question_number,
                question_text=q.question_text,
                question_category=q.question_category,
                scale_min=q.scale_min,
                scale_max=q.scale_max,
                scale_min_label=q.scale_min_label,
                scale_max_label=q.scale_max_label,
                is_required=q.is_required,
            )
            for q in sorted(survey.questions, key=lambda x: x.question_number)
        ],
        total_questions=len(survey.questions),
    )


@router.post("/answer", response_model=dict)
async def answer_survey_question(payload: SurveyAnswerRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Submit an answer for a survey question (Likert scale)."""
    survey_response_result = await db.execute(
        select(SurveyResponse).where(SurveyResponse.id == payload.response_id)
    )
    survey_response = survey_response_result.scalar_one_or_none()
    if not survey_response:
        raise HTTPException(status_code=404, detail="response_not_found")

    question_result = await db.execute(
        select(SurveyQuestion).where(SurveyQuestion.id == payload.question_id)
    )
    question = question_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="question_not_found")

    if payload.value < question.scale_min or payload.value > question.scale_max:
        raise HTTPException(
            status_code=400,
            detail=f"value must be between {question.scale_min} and {question.scale_max}"
        )

    existing_answer = await db.execute(
        select(SurveyAnswer)
        .where(SurveyAnswer.response_id == payload.response_id, SurveyAnswer.question_id == payload.question_id)
    )
    existing = existing_answer.scalar_one_or_none()

    if existing:
        existing.value = payload.value
        existing.text_response = payload.text_response
        answer = existing
    else:
        answer = SurveyAnswer(
            response_id=payload.response_id,
            question_id=payload.question_id,
            value=payload.value,
            text_response=payload.text_response,
        )
        db.add(answer)

    await db.commit()

    return {
        "question_id": payload.question_id,
        "value": payload.value,
        "answered": True,
    }


@router.post("/complete", response_model=SurveyCompleteResponse)
async def complete_survey(payload: SurveyCompleteRequest, db: AsyncSession = Depends(get_db)) -> SurveyCompleteResponse:
    """Mark a survey as complete."""
    response_result = await db.execute(
        select(SurveyResponse)
        .where(SurveyResponse.id == payload.response_id)
        .options(selectinload(SurveyResponse.answers))
    )
    survey_response = response_result.scalar_one_or_none()
    if not survey_response:
        raise HTTPException(status_code=404, detail="response_not_found")

    if survey_response.is_complete:
        raise HTTPException(status_code=400, detail="survey_already_completed")

    survey_result = await db.execute(
        select(Survey)
        .where(Survey.id == survey_response.survey_id)
        .options(selectinload(Survey.questions))
    )
    survey = survey_result.scalar_one()

    required_questions = [q for q in survey.questions if q.is_required]
    answered_ids = {a.question_id for a in survey_response.answers}

    unanswered_required = [
        q.question_number for q in required_questions if q.id not in answered_ids
    ]
    if unanswered_required:
        raise HTTPException(
            status_code=400,
            detail=f"Please answer all required questions. Missing: {unanswered_required}"
        )

    survey_response.is_complete = True
    survey_response.completed_at = datetime.utcnow()

    await db.commit()

    return SurveyCompleteResponse(
        response_id=survey_response.id,
        is_complete=True,
        questions_answered=len(survey_response.answers),
        completed_at=survey_response.completed_at,
    )


@router.get("/responses/{session_id}", response_model=list[dict])
async def get_session_survey_responses(session_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Get all survey responses for a session."""
    result = await db.execute(
        select(SurveyResponse)
        .where(SurveyResponse.session_id == session_id)
        .options(selectinload(SurveyResponse.answers))
        .order_by(SurveyResponse.started_at.desc())
    )
    responses = result.scalars().all()
    return [
        {
            "id": r.id,
            "survey_id": r.survey_id,
            "is_complete": r.is_complete,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "answers": [
                {"question_id": a.question_id, "value": a.value, "text_response": a.text_response}
                for a in r.answers
            ],
        }
        for r in responses
    ]


@router.get("/stats/{survey_id}", response_model=SurveyStatsResponse)
async def get_survey_stats(survey_id: str, db: AsyncSession = Depends(get_db)) -> SurveyStatsResponse:
    """Get aggregated statistics for a survey (admin endpoint)."""
    survey_result = await db.execute(
        select(Survey)
        .where(Survey.id == survey_id)
        .options(selectinload(Survey.questions))
    )
    survey = survey_result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="survey_not_found")

    responses_result = await db.execute(
        select(SurveyResponse)
        .where(SurveyResponse.survey_id == survey_id, SurveyResponse.is_complete == True)
        .options(selectinload(SurveyResponse.answers))
    )
    responses = responses_result.scalars().all()

    question_totals: dict[int, list[int]] = {q.id: [] for q in survey.questions}
    for resp in responses:
        for answer in resp.answers:
            if answer.question_id in question_totals:
                question_totals[answer.question_id].append(answer.value)

    average_by_question: dict[int, float] = {}
    for q_id, values in question_totals.items():
        if values:
            average_by_question[q_id] = sum(values) / len(values)
        else:
            average_by_question[q_id] = 0.0

    category_totals: dict[str, list[int]] = {}
    category_counts: dict[str, int] = {}
    for q in survey.questions:
        if q.question_category:
            values = question_totals.get(q.id, [])
            if values:
                if q.question_category not in category_totals:
                    category_totals[q.question_category] = []
                    category_counts[q.question_category] = 0
                category_totals[q.question_category].extend(values)
                category_counts[q.question_category] += len(values)

    category_averages: dict[str, float] = {}
    for cat, values in category_totals.items():
        if values:
            category_averages[cat] = sum(values) / len(values)

    return SurveyStatsResponse(
        survey_id=survey_id,
        total_responses=len(responses),
        average_by_question=average_by_question,
        category_averages=category_averages,
    )
