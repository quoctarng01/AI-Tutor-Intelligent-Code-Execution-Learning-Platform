"""
Repository pattern for clean data access layer.
Provides a standardized interface for database operations.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

from backend.database import get_db


T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.
    Subclass this for each model to get type-safe access.
    """

    def __init__(self, model: type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: str | UUID) -> T | None:
        """Get a single record by primary key."""
        return await self.db.get(self.model, id)

    async def get_one(self, **filters) -> T | None:
        """Get a single record by filter criteria."""
        stmt = select(self.model).filter_by(**filters)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, **filters) -> list[T]:
        """Get all records matching filter criteria."""
        stmt = select(self.model).filter_by(**filters)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters) -> int:
        """Count records matching filter criteria."""
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def exists(self, **filters) -> bool:
        """Check if a record exists matching criteria."""
        count = await self.count(**filters)
        return count > 0


class ExerciseRepository(BaseRepository):
    """Repository for Exercise model."""

    def __init__(self, db: AsyncSession):
        from backend.models import Exercise

        super().__init__(Exercise, db)

    async def get_by_topic(self, topic: str) -> list[T]:
        """Get all exercises for a specific topic."""
        return await self.get_all(topic=topic)

    async def get_by_difficulty(self, difficulty: int) -> list[T]:
        """Get all exercises at a specific difficulty level."""
        return await self.get_all(difficulty=difficulty)

    async def get_ordered_by_id(self) -> list[T]:
        """Get all exercises ordered by ID."""
        stmt = select(self.model).order_by(self.model.id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class SessionRepository(BaseRepository):
    """Repository for Session model."""

    def __init__(self, db: AsyncSession):
        from backend.models import Session

        super().__init__(Session, db)

    async def get_by_username(self, username: str) -> list[T]:
        """Get all sessions for a username."""
        return await self.get_all(username=username)


class HintStateRepository(BaseRepository):
    """Repository for HintState model."""

    def __init__(self, db: AsyncSession):
        from backend.models import HintState

        super().__init__(HintState, db)

    async def get_for_session_exercise(
        self,
        session_id: str | UUID,
        exercise_id: str,
    ) -> T | None:
        """Get hint state for a specific session and exercise."""
        return await self.get_one(session_id=session_id, exercise_id=exercise_id)


class AttemptRepository(BaseRepository):
    """Repository for Attempt model."""

    def __init__(self, db: AsyncSession):
        from backend.models import Attempt

        super().__init__(Attempt, db)

    async def get_for_session(self, session_id: str | UUID) -> list[T]:
        """Get all attempts for a session."""
        return await self.get_all(session_id=session_id)

    async def get_for_exercise(self, exercise_id: str) -> list[T]:
        """Get all attempts for an exercise."""
        return await self.get_all(exercise_id=exercise_id)

    async def count_correct(self, session_id: str | UUID) -> int:
        """Count correct attempts for a session."""
        return await self.count(session_id=session_id, is_correct=True)


# Factory function for getting repositories
def get_repository(model_type: str, db: AsyncSession) -> BaseRepository:
    """
    Get a repository instance for the specified model type.

    Usage:
        repo = get_repository("exercise", db)
        exercises = await repo.get_ordered_by_id()
    """
    repositories = {
        "exercise": ExerciseRepository,
        "session": SessionRepository,
        "hint_state": HintStateRepository,
        "attempt": AttemptRepository,
    }

    repo_class = repositories.get(model_type.lower())
    if repo_class is None:
        raise ValueError(f"Unknown repository type: {model_type}")

    return repo_class(db)
