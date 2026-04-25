"""
Hint engine module for managing the 4-level progressive hint system.
Maintains hint state per session-exercise combination and handles hint progression.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import HintState

MAX_HINT_LEVEL = 4


class HintEngine:
    """
    State machine for managing progressive hint delivery.

    The hint system progresses through 4 levels:
    - L1/L2: Pre-authored hints stored in the database
    - L3/L4: LLM-generated hints (validated for answer leakage)

    Attributes:
        db: SQLAlchemy async session for database operations.

    Note:
        The HintState table is the authoritative source of hint level.
        Never compute hint level from hint_logs count to prevent manipulation.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the hint engine.

        Args:
            db: SQLAlchemy async session for database operations.
        """
        self.db = db

    async def _get_or_create_state(self, session_id: str, exercise_id: str) -> HintState:
        """
        Get or create hint state for a session-exercise pair.

        Args:
            session_id: The student's session UUID.
            exercise_id: The exercise identifier.

        Returns:
            HintState instance for the session-exercise combination.
        """
        result = await self.db.execute(
            select(HintState).where(
                HintState.session_id == session_id,
                HintState.exercise_id == exercise_id,
            )
        )
        state = result.scalar_one_or_none()
        if not state:
            state = HintState(
                session_id=session_id,
                exercise_id=exercise_id,
                current_level=0,
                is_solved=False,
            )
            self.db.add(state)
            await self.db.flush()
        return state

    async def request_hint(self, session_id: str, exercise_id: str) -> dict:
        """
        Request the next hint level for an exercise.

        Advances the hint level by 1 and returns the new level.
        Returns error if already solved or hints exhausted.

        Args:
            session_id: The student's session UUID.
            exercise_id: The exercise identifier.

        Returns:
            Dict with 'level' and 'is_final' keys on success,
            or 'error' key with error code on failure.
        """
        state = await self._get_or_create_state(session_id, exercise_id)
        if state.is_solved:
            return {"error": "exercise_already_solved", "level": None}
        if state.current_level >= MAX_HINT_LEVEL:
            return {"error": "hints_exhausted", "level": state.current_level}

        state.current_level += 1
        await self.db.commit()
        return {"level": state.current_level, "is_final": state.current_level == MAX_HINT_LEVEL}

    async def mark_solved(self, session_id: str, exercise_id: str) -> None:
        """
        Mark an exercise as solved for a session.

        Called when a correct submission is received.
        Prevents further hint requests for this exercise.

        Args:
            session_id: The student's session UUID.
            exercise_id: The exercise identifier.
        """
        state = await self._get_or_create_state(session_id, exercise_id)
        state.is_solved = True
        await self.db.commit()

    async def get_state(self, session_id: str, exercise_id: str) -> dict:
        """
        Get the current hint state for an exercise.

        Args:
            session_id: The student's session UUID.
            exercise_id: The exercise identifier.

        Returns:
            Dict containing:
                - current_level: Current hint level (0-4)
                - is_solved: Whether the exercise has been solved
                - is_exhausted: Whether all hints have been requested
        """
        state = await self._get_or_create_state(session_id, exercise_id)
        return {
            "current_level": state.current_level,
            "is_solved": state.is_solved,
            "is_exhausted": state.current_level >= MAX_HINT_LEVEL and not state.is_solved,
        }
