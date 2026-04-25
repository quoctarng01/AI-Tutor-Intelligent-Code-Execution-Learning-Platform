"""
Pytest configuration and fixtures for AI Tutor tests.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_session_id() -> str:
    """Generate a mock session ID."""
    return str(uuid4())


@pytest.fixture
def mock_exercise_id() -> str:
    """Generate a mock exercise ID."""
    return "loops_001"


@pytest.fixture
def mock_user_data() -> dict[str, Any]:
    """Mock user data for testing."""
    return {
        "username": "test_user",
        "group_type": "tutor",
        "session_id": str(uuid4()),
    }


@pytest.fixture
def mock_jwt_token(mock_user_data: dict[str, Any]) -> str:
    """Generate a mock JWT token for testing."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt

    secret = "test-secret-key-for-testing-only"
    payload = {
        "sub": mock_user_data["username"],
        "session_id": mock_user_data["session_id"],
        "group_type": mock_user_data["group_type"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def mock_exercise() -> MagicMock:
    """Create a mock exercise object."""
    exercise = MagicMock()
    exercise.id = "loops_001"
    exercise.topic = "loops"
    exercise.title = "Print Numbers 1 to N"
    exercise.problem_statement = "Write a for loop that prints all integers from 1 to N."
    exercise.hint_l1 = "A for loop repeats a block of code."
    exercise.hint_l2 = "Think about where range() should start and end."
    exercise.concept = "for loop with range"
    exercise.correct_criteria = {
        "type": "code_execution",
        "test_cases": [
            {"input": "5", "expected_output": "1\n2\n3\n4\n5"},
        ],
    }
    return exercise


@pytest.fixture
def sample_python_code() -> str:
    """Sample valid Python code for testing."""
    return '''
for i in range(1, 6):
    print(i)
'''


@pytest.fixture
def malicious_python_code() -> str:
    """Sample malicious Python code for testing sandbox."""
    return '''
import os
os.system("rm -rf /")
'''


@pytest.fixture
def syntax_error_code() -> str:
    """Python code with syntax errors."""
    return '''
for i in range(1, 6)
    print(i)
'''


@pytest.fixture
def infinite_loop_code() -> str:
    """Python code with infinite loop."""
    return '''
while True:
    print("infinite")
'''


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    return session


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Create a mock cache service."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    cache.exists = AsyncMock(return_value=False)
    return cache


@pytest.fixture
def mock_rate_limiter() -> AsyncMock:
    """Create a mock rate limiter."""
    limiter = AsyncMock()
    limiter.check_limit = AsyncMock(return_value=MagicMock(
        limit=60,
        remaining=59,
        reset_at=0,
        window_seconds=60,
    ))
    limiter.increment = AsyncMock(return_value=(True, MagicMock(
        limit=60,
        remaining=58,
        reset_at=0,
        window_seconds=60,
    )))
    return limiter


@pytest.fixture
def mock_llm_response() -> str:
    """Mock LLM response for testing."""
    return "Think about using range() to generate the sequence of numbers."
