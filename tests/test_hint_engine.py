"""
Unit tests for the hint engine.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.services.hint_engine import HintEngine, MAX_HINT_LEVEL


class TestHintEngine:
    """Tests for HintEngine state machine."""

    @pytest.fixture
    def engine(self, mock_db_session: AsyncMock) -> HintEngine:
        """Create a HintEngine instance with mocked DB."""
        return HintEngine(mock_db_session)

    @pytest.mark.asyncio
    async def test_request_first_hint(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test requesting the first hint."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_db_session.commit = AsyncMock()

        result = await engine.request_hint("session_1", "exercise_1")

        assert result["level"] == 1
        assert result["is_final"] is False

    @pytest.mark.asyncio
    async def test_request_hint_sequence(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test requesting hints in sequence."""
        # First hint
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        result = await engine.request_hint("session_1", "exercise_1")
        assert result["level"] == 1

        # Second hint - state exists with level 1
        state = MagicMock()
        state.current_level = 1
        state.is_solved = False
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = state

        result = await engine.request_hint("session_1", "exercise_1")
        assert result["level"] == 2

    @pytest.mark.asyncio
    async def test_cannot_request_hints_after_solved(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test that hints cannot be requested after exercise is solved."""
        state = MagicMock()
        state.is_solved = True
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = state

        result = await engine.request_hint("session_1", "exercise_1")

        assert "error" in result
        assert result["error"] == "exercise_already_solved"

    @pytest.mark.asyncio
    async def test_hints_exhausted_at_level_4(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test that hints are exhausted at level 4."""
        state = MagicMock()
        state.current_level = 4
        state.is_solved = False
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = state

        result = await engine.request_hint("session_1", "exercise_1")

        assert "error" in result
        assert result["error"] == "hints_exhausted"
        assert result["level"] == 4

    @pytest.mark.asyncio
    async def test_mark_solved(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test marking an exercise as solved."""
        state = MagicMock()
        state.is_solved = False
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = state
        mock_db_session.commit = AsyncMock()

        await engine.mark_solved("session_1", "exercise_1")

        assert state.is_solved is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_state_new_session(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test getting state for new session."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_db_session.flush = AsyncMock()
        mock_db_session.add = MagicMock()

        state = await engine.get_state("session_1", "exercise_1")

        assert state["current_level"] == 0
        assert state["is_solved"] is False
        assert state["is_exhausted"] is False

    @pytest.mark.asyncio
    async def test_get_state_existing_session(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test getting state for existing session."""
        state = MagicMock()
        state.current_level = 2
        state.is_solved = False
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = state

        result = await engine.get_state("session_1", "exercise_1")

        assert result["current_level"] == 2
        assert result["is_solved"] is False
        assert result["is_exhausted"] is False

    @pytest.mark.asyncio
    async def test_get_state_exhausted(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test getting state when hints are exhausted."""
        state = MagicMock()
        state.current_level = 4
        state.is_solved = False
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = state

        result = await engine.get_state("session_1", "exercise_1")

        assert result["is_exhausted"] is True

    @pytest.mark.asyncio
    async def test_state_created_on_first_request(self, engine: HintEngine, mock_db_session: AsyncMock):
        """Test that state is created on first hint request."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_db_session.add = MagicMock()
        mock_db_session.flush = AsyncMock()
        mock_db_session.commit = AsyncMock()

        await engine.request_hint("session_1", "exercise_1")

        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()


class TestHintEngineConstants:
    """Tests for hint engine constants."""

    def test_max_hint_level(self):
        """Test that MAX_HINT_LEVEL is 4."""
        assert MAX_HINT_LEVEL == 4
