"""
Hint system router with 4-level progressive hints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Exercise
from backend.schemas import HintRequest, HintResponse
from backend.security import get_current_user, TokenData
from backend.services import (
    HintEngine,
    get_llm_client,
    LeakageValidator,
    PromptBuilder,
    get_rate_limiter,
    get_cache_service,
    log_hint,
)
from backend.services.logging_service import get_logger, set_request_context
from backend.exceptions import RateLimitError, LLMServiceError


router = APIRouter(prefix="/hint", tags=["hints"])
logger = get_logger("hints")

# Fallback hints for when LLM validation fails
L3_FALLBACK = (
    "Think about breaking this problem into smaller steps. What is the first "
    "logical action you need to take? Try describing the approach in plain English "
    "before writing any code."
)

L4_FALLBACK = (
    "Here's a structured approach:\n\n"
    "1. Identify what data you need to work with\n"
    "2. Determine the operations required\n"
    "3. Decide on the order of operations\n\n"
    "Focus on step 1 first. What information do you need, and where does it come from?"
)


@router.post(
    "/",
    response_model=HintResponse,
    summary="Request the next hint level",
    description="Request the next level of hint for the current exercise. Hints progress from L1 to L4.",
    responses={
        200: {"description": "Hint delivered"},
        400: {"description": "No more hints available or exercise already solved"},
        404: {"description": "Exercise not found"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "LLM service unavailable"},
    },
)
async def request_hint(
    body: HintRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> HintResponse:
    """
    Request the next level hint for an exercise.
    - L1/L2: Pre-authored hints (returned immediately)
    - L3/L4: LLM-generated hints (validated before delivery)
    """
    # Set request context for logging
    set_request_context(
        request.headers.get("X-Request-ID", ""),
        body.session_id,
    )

    # Rate limit hint requests (LLM hints are more expensive)
    rate_limiter = get_rate_limiter()
    rate_key = f"hint:{body.session_id}:{body.exercise_id}"

    # Only rate limit LLM-generated hints (L3/L4)
    limit_type = "hint"
    is_allowed, limit_info = await rate_limiter.increment(rate_key, limit_type, window_seconds=60)

    if not is_allowed:
        logger.warning(
            "hint_rate_limited",
            session_id=str(body.session_id),
            exercise_id=body.exercise_id,
        )
        raise RateLimitError(retry_after=int(limit_info.reset_at - __import__("time").time()))

    # Verify session ownership
    if str(current_user.session_id) != str(body.session_id):
        raise HTTPException(status_code=403, detail="Not authorized for this session")

    # Get hint engine and request next level
    engine = HintEngine(db)
    result = await engine.request_hint(str(body.session_id), body.exercise_id)

    if "error" in result:
        if result["error"] == "exercise_already_solved":
            raise HTTPException(status_code=400, detail="exercise_already_solved")
        if result["error"] == "hints_exhausted":
            raise HTTPException(status_code=400, detail="hints_exhausted")
        raise HTTPException(status_code=400, detail=result["error"])

    level = result["level"]

    # Fetch exercise for hint content
    exercise = await db.get(Exercise, body.exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="exercise_not_found")

    # L1/L2: Pre-authored hints
    if level <= 2:
        hint_text = exercise.hint_l1 if level == 1 else exercise.hint_l2
        await log_hint(
            db,
            body.session_id,
            body.exercise_id,
            level,
            f"pre_authored_l{level}",
            "",
            hint_text,
            was_pre_authored=True,
        )
        return HintResponse(level=level, hint=hint_text, is_final=False)

    # L3/L4: LLM-generated hints
    prompt_version = f"hint_l{level}_v1"

    # Check cache for generated hints
    cache = get_cache_service()
    cache_key = f"hint_gen:{body.exercise_id}:{level}"
    cached_hint = await cache.get(cache_key)

    if cached_hint:
        hint_text = cached_hint
        logger.debug("hint_cache_hit", exercise_id=body.exercise_id, level=level)
    else:
        # Generate hint with LLM
        builder = PromptBuilder()
        system_prompt, user_prompt = builder.build(prompt_version, exercise)

        llm = get_llm_client()

        try:
            raw_response = await llm.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
                max_tokens=500,
                retries=2,
            )
        except LLMServiceError as e:
            logger.error("llm_hint_generation_failed", error=str(e))
            raise HTTPException(
                status_code=503,
                detail="AI service temporarily unavailable. Please try again.",
            )

        # Validate hint for answer leakage
        validator = LeakageValidator()
        validation_result = validator.check(raw_response, exercise, level)

        if validation_result.is_valid:
            hint_text = raw_response
            # Cache valid hints
            await cache.set(cache_key, hint_text, ttl=3600)  # Cache for 1 hour
        else:
            # Use fallback for validation failures
            logger.warning(
                "hint_validation_failed",
                level=level,
                exercise_id=body.exercise_id,
                reason=validation_result.reason,
            )
            hint_text = L3_FALLBACK if level == 3 else L4_FALLBACK

    # Log the hint delivery
    await log_hint(
        db,
        body.session_id,
        body.exercise_id,
        level,
        prompt_version,
        f"hint_generated_{level}",
        hint_text,
        was_pre_authored=False,
    )

    logger.info(
        "hint_delivered",
        session_id=str(body.session_id),
        exercise_id=body.exercise_id,
        level=level,
        is_final=(level == 4),
    )

    return HintResponse(level=level, hint=hint_text, is_final=(level == 4))


@router.get(
    "/state/{session_id}/{exercise_id}",
    response_model=dict,
    summary="Get hint state for an exercise",
    description="Get the current hint state for a session-exercise combination.",
)
async def get_hint_state(
    session_id: str,
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    """Get the current hint state for an exercise."""
    # Verify session ownership
    if str(current_user.session_id) != session_id:
        raise HTTPException(status_code=403, detail="Not authorized for this session")

    engine = HintEngine(db)
    state = await engine.get_state(session_id, exercise_id)

    return {
        "current_level": state["current_level"],
        "is_solved": state["is_solved"],
        "is_exhausted": state["is_exhausted"],
        "max_level": 4,
    }
