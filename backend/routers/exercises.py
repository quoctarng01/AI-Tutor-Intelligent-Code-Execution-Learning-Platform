"""
Exercises router for listing and retrieving Python exercises.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Exercise
from backend.schemas import ExerciseResponse
from backend.security import get_current_user, TokenData
from backend.services import get_cache_service
from backend.services.logging_service import get_logger


router = APIRouter(prefix="/exercises", tags=["exercises"])
logger = get_logger("exercises")


@router.get(
    "",
    response_model=list[ExerciseResponse],
    summary="List all exercises",
    description="Retrieve all available Python exercises. Requires authentication.",
    responses={
        200: {"description": "List of exercises"},
        401: {"description": "Authentication required"},
    },
)
async def list_exercises(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    topic: str | None = None,
    difficulty: int | None = None,
) -> list[ExerciseResponse]:
    """List all available exercises with optional filtering."""
    cache = get_cache_service()

    # Build cache key based on filters
    cache_key = f"exercises:list:{topic or 'all'}:{difficulty or 'all'}"

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        logger.debug("exercises_cache_hit", topic=topic, difficulty=difficulty)
        return cached

    # Query database
    query = select(Exercise).order_by(Exercise.id)

    if topic:
        query = query.where(Exercise.topic == topic)
    if difficulty:
        query = query.where(Exercise.difficulty == difficulty)

    result = await db.execute(query)
    exercises = result.scalars().all()

    # Transform to response format
    response = [ExerciseResponse.model_validate(ex) for ex in exercises]

    # Cache the result
    await cache.set(cache_key, [e.model_dump() for e in response], ttl=300)

    logger.info(
        "exercises_listed",
        count=len(exercises),
        topic=topic,
        difficulty=difficulty,
    )

    return response


@router.get(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Get exercise by ID",
    description="Retrieve a specific exercise by its ID. Requires authentication.",
    responses={
        200: {"description": "Exercise details"},
        401: {"description": "Authentication required"},
        404: {"description": "Exercise not found"},
    },
)
async def get_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> ExerciseResponse:
    """Get a specific exercise by ID."""
    cache = get_cache_service()
    cache_key = f"exercise:{exercise_id}"

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        logger.debug("exercise_cache_hit", exercise_id=exercise_id)
        return ExerciseResponse(**cached)

    # Query database
    exercise = await db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="exercise_not_found")

    response = ExerciseResponse.model_validate(exercise)

    # Cache the result
    await cache.set(cache_key, response.model_dump(), ttl=600)

    return response


@router.get(
    "/{exercise_id}/next",
    response_model=ExerciseResponse,
    summary="Get next exercise",
    description="Get the next exercise in sequence after the current one. Requires authentication.",
    responses={
        200: {"description": "Next exercise"},
        401: {"description": "Authentication required"},
        404: {"description": "No exercises found"},
    },
)
async def get_next_exercise(
    exercise_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> ExerciseResponse:
    """Get the next exercise in the sequence."""
    cache = get_cache_service()
    cache_key = f"exercises:list:all:all"

    # Get cached or fresh list
    cached = await cache.get(cache_key)
    if cached:
        exercises_data = cached
    else:
        result = await db.execute(select(Exercise).order_by(Exercise.id))
        exercises_data = [
            ExerciseResponse.model_validate(ex).model_dump()
            for ex in result.scalars().all()
        ]

    if not exercises_data:
        raise HTTPException(status_code=404, detail="no_exercises")

    ids = [ex["id"] for ex in exercises_data]

    if exercise_id not in ids:
        raise HTTPException(status_code=404, detail="exercise_not_found")

    idx = ids.index(exercise_id)
    next_idx = (idx + 1) % len(exercises_data)
    next_exercise_data = exercises_data[next_idx]

    logger.info(
        "next_exercise_requested",
        current_exercise=exercise_id,
        next_exercise=next_exercise_data["id"],
    )

    return ExerciseResponse(**next_exercise_data)


@router.get(
    "/topics",
    response_model=list[dict],
    summary="List available topics",
    description="Get all unique exercise topics. Requires authentication.",
)
async def list_topics(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> list[dict]:
    """Get all available exercise topics with counts."""
    cache = get_cache_service()
    cache_key = "exercises:topics"

    cached = await cache.get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(Exercise.topic, Exercise.difficulty).order_by(Exercise.topic)
    )
    rows = result.all()

    # Group by topic
    topics: dict[str, dict] = {}
    for topic, difficulty in rows:
        if topic not in topics:
            topics[topic] = {"topic": topic, "count": 0, "min_difficulty": 10, "max_difficulty": 0}
        topics[topic]["count"] += 1
        topics[topic]["min_difficulty"] = min(topics[topic]["min_difficulty"], difficulty or 0)
        topics[topic]["max_difficulty"] = max(topics[topic]["max_difficulty"], difficulty or 0)

    response = list(topics.values())
    await cache.set(cache_key, response, ttl=600)

    return response
