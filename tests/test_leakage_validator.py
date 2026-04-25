"""
Unit tests for the leakage validator.
"""

import pytest

from backend.services.output_validator import LeakageValidator, ValidationResult


class TestLeakageValidator:
    """Tests for hint leakage detection."""

    @pytest.fixture
    def validator(self) -> LeakageValidator:
        """Create a validator instance."""
        return LeakageValidator()

    @pytest.fixture
    def mock_exercise(self):
        """Create a mock exercise."""
        exercise = type("Exercise", (), {
            "concept": "for loop with range"
        })()
        return exercise

    # Valid hint tests
    def test_valid_educational_hint(self, validator: LeakageValidator, mock_exercise):
        """Test that valid educational hints pass."""
        hint = "A for loop repeats code a specific number of times. The range() function generates a sequence of numbers."
        result = validator.check(hint, mock_exercise, level=1)
        assert result.is_valid is True

    def test_valid_hint_with_question(self, validator: LeakageValidator, mock_exercise):
        """Test that hints with questions are valid."""
        hint = "Think about where range() should start and end. What happens with range(N) vs range(1, N+1)?"
        result = validator.check(hint, mock_exercise, level=2)
        assert result.is_valid is True

    def test_valid_hint_with_analogy(self, validator: LeakageValidator, mock_exercise):
        """Test that hints with analogies are valid."""
        hint = "Think of a loop like a recipe. Each step needs to be repeated until you're done."
        result = validator.check(hint, mock_exercise, level=3)
        assert result.is_valid is True

    def test_valid_long_hint(self, validator: LeakageValidator, mock_exercise):
        """Test that longer educational hints are valid."""
        hint = "Here's a structured approach to solving this problem:\n\n1. Identify what data you need to work with\n2. Determine the operations required\n3. Decide on the order of operations"
        result = validator.check(hint, mock_exercise, level=4)
        assert result.is_valid is True

    # Level 1 specific tests
    def test_l1_blocks_code_blocks(self, validator: LeakageValidator, mock_exercise):
        """Test that L1 hints cannot contain code blocks."""
        hint = "Use this code:\n```python\nfor i in range(1, 6):\n    print(i)\n```"
        result = validator.check(hint, mock_exercise, level=1)
        assert result.is_valid is False

    def test_l1_blocks_function_definitions(self, validator: LeakageValidator, mock_exercise):
        """Test that L1 hints cannot contain function definitions."""
        hint = "You should def calculate(): return value"
        result = validator.check(hint, mock_exercise, level=1)
        assert result.is_valid is False

    def test_l1_blocks_return_statement(self, validator: LeakageValidator, mock_exercise):
        """Test that L1 hints cannot contain return statements."""
        hint = "Make sure to return the correct value"
        result = validator.check(hint, mock_exercise, level=1)
        assert result.is_valid is False

    def test_l1_blocks_print_function(self, validator: LeakageValidator, mock_exercise):
        """Test that L1 hints cannot mention print()."""
        hint = "Use print() to display output"
        result = validator.check(hint, mock_exercise, level=1)
        assert result.is_valid is False

    # Solution leakage tests
    def test_blocks_direct_solution(self, validator: LeakageValidator, mock_exercise):
        """Test that direct solution statements are blocked."""
        hint = "Here's the solution: for i in range(1, 6): print(i)"
        result = validator.check(hint, mock_exercise, level=2)
        assert result.is_valid is False

    def test_blocks_correct_answer_mention(self, validator: LeakageValidator, mock_exercise):
        """Test that mentioning 'correct answer' is blocked."""
        hint = "The correct answer is to use range(1, N+1)"
        result = validator.check(hint, mock_exercise, level=2)
        assert result.is_valid is False

    def test_blocks_code_suggestion(self, validator: LeakageValidator, mock_exercise):
        """Test that inline code suggestions are blocked."""
        hint = "You should write `for i in range(1, 6)`"
        result = validator.check(hint, mock_exercise, level=2)
        assert result.is_valid is False

    def test_blocks_function_call_suggestion(self, validator: LeakageValidator, mock_exercise):
        """Test that function call suggestions are blocked."""
        hint = "You can use print(i) to output"
        result = validator.check(hint, mock_exercise, level=2)
        assert result.is_valid is False

    def test_blocks_try_this_pattern(self, validator: LeakageValidator, mock_exercise):
        """Test that 'try this' patterns are blocked."""
        hint = "Try this:\nfor i in range(1, 6):\n    print(i)"
        result = validator.check(hint, mock_exercise, level=3)
        assert result.is_valid is False

    def test_blocks_minimization_language(self, validator: LeakageValidator, mock_exercise):
        """Test that minimization language triggers warnings."""
        hint = "Just use for i in range(1, 6) and print(i)"
        result = validator.check(hint, mock_exercise, level=3)
        assert result.is_valid is False

    # Length tests
    def test_rejects_empty_hint(self, validator: LeakageValidator, mock_exercise):
        """Test that empty hints are rejected."""
        result = validator.check("", mock_exercise, level=1)
        assert result.is_valid is False
        assert result.reason == "empty_response"

    def test_rejects_too_short_hint_l1(self, validator: LeakageValidator, mock_exercise):
        """Test that very short hints are rejected for L1."""
        result = validator.check("Use range.", mock_exercise, level=1)
        assert result.is_valid is False
        assert "too_short" in result.reason

    # Case insensitive tests
    def test_case_insensitive_detection(self, validator: LeakageValidator, mock_exercise):
        """Test that detection is case insensitive."""
        hint = "Here's THE SOLUTION: for i in range(1, 6)"
        result = validator.check(hint, mock_exercise, level=3)
        assert result.is_valid is False


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(is_valid=True, reason="ok")
        assert result.is_valid is True
        assert result.reason == "ok"

    def test_invalid_result_with_details(self):
        """Test creating an invalid result with details."""
        result = ValidationResult(
            is_valid=False,
            reason="forbidden_words",
            details={"forbidden_words": ["answer", "solution"]}
        )
        assert result.is_valid is False
        assert result.reason == "forbidden_words"
        assert "answer" in result.details["forbidden_words"]

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = ValidationResult(is_valid=True, reason="ok", details={"level": 2})
        d = result.to_dict()
        assert d["is_valid"] is True
        assert d["reason"] == "ok"
        assert d["details"]["level"] == 2
