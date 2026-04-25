"""
Code submission router for evaluating student solutions.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Attempt, Exercise
from backend.schemas import SubmitRequest, SubmitResponse
from backend.security import get_current_user, TokenData
from backend.services import (
    evaluate_code,
    HintEngine,
    get_rate_limiter,
)
from backend.services.logging_service import get_logger, set_request_context
from backend.services.secure_sandbox import validate_code_syntax
from backend.exceptions import RateLimitError, SandboxError


router = APIRouter(tags=["submit"])
logger = get_logger("submit")


@router.post(
    "/submit",
    response_model=SubmitResponse,
    summary="Submit code for evaluation",
    description="Submit student code for evaluation against test cases.",
    responses={
        200: {"description": "Code evaluated successfully"},
        400: {"description": "Invalid code or validation error"},
        404: {"description": "Exercise not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def submit_answer(
    body: SubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> SubmitResponse:
    """
    Submit code for evaluation.
    The code is validated for syntax and security, then executed against test cases.
    """
    # Set request context for logging
    set_request_context(
        request.headers.get("X-Request-ID", ""),
        body.session_id,
    )

    # Rate limit submissions
    rate_limiter = get_rate_limiter()
    rate_key = f"submit:{body.session_id}"
    is_allowed, _ = await rate_limiter.increment(rate_key, "submit", window_seconds=60)

    if not is_allowed:
        logger.warning("submit_rate_limited", session_id=str(body.session_id))
        raise RateLimitError(retry_after=60)

    # Verify session ownership
    if str(current_user.session_id) != str(body.session_id):
        raise HTTPException(status_code=403, detail="Not authorized for this session")

    # Validate code syntax and security before execution
    validation = validate_code_syntax(body.code)
    if not validation.is_valid:
        logger.warning(
            "code_validation_failed",
            session_id=str(body.session_id),
            exercise_id=body.exercise_id,
            error=validation.error,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Code validation failed: {validation.error}",
        )

    # Fetch exercise
    exercise = await db.get(Exercise, body.exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="exercise_not_found")

    # Get current hint state
    engine = HintEngine(db)
    hint_state = await engine.get_state(str(body.session_id), body.exercise_id)

    # Evaluate code
    criteria = exercise.correct_criteria
    criteria_type = criteria.get("type")

    try:
        if criteria_type == "code_execution":
            test_cases = criteria.get("test_cases", [])
            if not test_cases:
                raise HTTPException(
                    status_code=500,
                    detail="No test cases configured for this exercise",
                )

            result = await evaluate_code(body.code, test_cases)
            is_correct = result.get("passed", False)

            # Log submission details
            logger.info(
                "code_submitted",
                session_id=str(body.session_id),
                exercise_id=body.exercise_id,
                is_correct=is_correct,
                tests_passed=result.get("passed_count", 0),
                tests_total=result.get("total", 0),
                hints_used=hint_state["current_level"],
            )

        elif criteria_type == "llm_judge":
            # LLM judge uses rubric-based evaluation
            # Note: This is a simplified implementation
            # A production system would use a more sophisticated approach
            rubric = criteria.get("rubric", {})
            must_contain = rubric.get("must_contain", [])
            lowered = body.code.lower()
            is_correct = all(token.lower() in lowered for token in must_contain)
            logger.info(
                "llm_judge_submitted",
                session_id=str(body.session_id),
                exercise_id=body.exercise_id,
                is_correct=is_correct,
            )

        elif criteria_type == "exact_match":
            expected = criteria.get("expected", "")
            is_correct = body.code.strip() == str(expected).strip()
            logger.info(
                "exact_match_submitted",
                session_id=str(body.session_id),
                exercise_id=body.exercise_id,
                is_correct=is_correct,
            )

        else:
            raise HTTPException(
                status_code=500,
                detail=f"Unknown criteria type: {criteria_type}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "submission_error",
            session_id=str(body.session_id),
            exercise_id=body.exercise_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to evaluate submission",
        )

    # Record the attempt
    try:
        await db.execute(
            insert(Attempt).values(
                session_id=body.session_id,
                exercise_id=body.exercise_id,
                submitted_code=body.code,
                is_correct=is_correct,
                hints_used=hint_state["current_level"],
                time_to_solve_s=body.elapsed_seconds,
                hint_state=f"HINT_{hint_state['current_level']}" if hint_state["current_level"] > 0 else "IDLE",
            )
        )

        # Mark exercise as solved if correct
        if is_correct:
            await engine.mark_solved(str(body.session_id), body.exercise_id)
            logger.info(
                "exercise_solved",
                session_id=str(body.session_id),
                exercise_id=body.exercise_id,
                hints_used=hint_state["current_level"],
                time_to_solve_s=body.elapsed_seconds,
            )
        else:
            await db.commit()

    except Exception as e:
        logger.error(
            "attempt_log_failed",
            session_id=str(body.session_id),
            exercise_id=body.exercise_id,
            error=str(e),
        )
        # Don't fail the submission if logging fails

    return SubmitResponse(
        is_correct=is_correct,
        hints_used=hint_state["current_level"],
    )
