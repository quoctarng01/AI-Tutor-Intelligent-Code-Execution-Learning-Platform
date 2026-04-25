#!/usr/bin/env python3
"""
Test script for LLM Hint Generation System.
Tests leakage validation, hint generation, and prompt loading.

Usage:
    python backend/scripts/test_hint_system.py
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.output_validator import LeakageValidator, ValidationResult
from backend.services.prompt_builder import PromptBuilder


class MockExercise:
    """Mock exercise object for testing."""
    def __init__(self, concept: str, llm_context: str, common_mistakes: list = None):
        self.id = "test_001"
        self.title = "Test Exercise"
        self.concept = concept
        self.llm_context = llm_context
        self.common_mistakes = common_mistakes or ["common mistake 1", "common mistake 2"]


def test_leakage_validator():
    """Test the leakage validator with various inputs."""
    print("\n" + "=" * 60)
    print("TESTING LEAKAGE VALIDATOR")
    print("=" * 60)
    
    validator = LeakageValidator()
    test_cases = [
        # Valid hints (should pass)
        {
            "name": "Valid L1 hint",
            "text": "Loops repeat a block of code a fixed number of times based on range().",
            "level": 1,
            "expected": True,
        },
        {
            "name": "Valid L2 hint (ends with question)",
            "text": "Think about where the loop should start and end. What happens with inclusive vs exclusive bounds?",
            "level": 2,
            "expected": True,
        },
        {
            "name": "Valid L3 pseudocode hint (with concept)",
            "text": "Think of it like a recipe: first gather your ingredients, then combine them in order, finally present the result. This for loop approach helps you process each item systematically.",
            "level": 3,
            "expected": True,
        },
        {
            "name": "Valid L4 structured hint",
            "text": "Step 1: Initialize your counter variable. Step 2: Set up your while condition. Step 3: Inside the loop, update the counter and print.",
            "level": 4,
            "expected": True,
        },
        
        # Invalid hints (should fail)
        {
            "name": "Direct solution statement",
            "text": "Here's the solution: def greet(name): return f'Hello, {name}!'",
            "level": 1,
            "expected": False,
        },
        {
            "name": "Complete function definition",
            "text": "The answer is to write def calculate(x): return x * 2",
            "level": 1,
            "expected": False,
        },
        {
            "name": "Code block in L1",
            "text": "```python\nfor i in range(5):\n    print(i)\n```",
            "level": 1,
            "expected": False,
        },
        {
            "name": "Code block in L2",
            "text": "Use this pattern: for i in range(N): print(i)",
            "level": 2,
            "expected": False,
        },
        {
            "name": "Forbidden word 'solution'",
            "text": "The solution involves using a for loop to iterate.",
            "level": 1,
            "expected": False,
        },
        {
            "name": "Forbidden word 'answer'",
            "text": "The answer is to check if n % 2 equals 0.",
            "level": 2,
            "expected": False,
        },
        {
            "name": "Irrelevant content",
            "text": "Python has many built-in functions.",
            "level": 1,
            "expected": False,
        },
        {
            "name": "Too short",
            "text": "Use a loop.",
            "level": 1,
            "expected": False,
        },
    ]
    
    passed = 0
    failed = 0
    
    exercise = MockExercise(
        concept="for loop with range",
        llm_context="Student is learning for loops with range()",
    )
    
    for tc in test_cases:
        result = validator.check(tc["text"], exercise, tc["level"])
        status = "PASS" if result.is_valid == tc["expected"] else "FAIL"
        
        if result.is_valid == tc["expected"]:
            passed += 1
            print(f"  [{status}] {tc['name']}")
        else:
            failed += 1
            print(f"  [{status}] {tc['name']}")
            print(f"         Expected: {'Valid' if tc['expected'] else 'Invalid'}")
            print(f"         Got: {'Valid' if result.is_valid else f'Invalid ({result.reason})'}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_prompt_builder():
    """Test YAML prompt template loading."""
    print("\n" + "=" * 60)
    print("TESTING PROMPT BUILDER")
    print("=" * 60)
    
    builder = PromptBuilder()
    
    # Test loading each level
    levels = [1, 2, 3, 4]
    exercise = MockExercise(
        concept="for loop with range",
        llm_context="Student is learning for loops with range(). Common errors: range(N) vs range(1,N+1), off-by-one errors.",
        common_mistakes=["using range(N) instead of range(1, N+1)", "printing N instead of the loop variable"],
    )
    
    passed = 0
    failed = 0
    
    for level in levels:
        try:
            prompt_version = f"hint_l{level}_v1"
            system_prompt, user_prompt = builder.build(prompt_version, exercise)
            
            if system_prompt and user_prompt:
                print(f"  [PASS] L{level} prompt loaded ({len(system_prompt)} + {len(user_prompt)} chars)")
                passed += 1
                
                # Verify placeholders are replaced
                placeholders_remaining = [
                    "{concept}", "{llm_context}", "{common_mistakes}",
                    "{title}", "{exercise_id}",
                ]
                for ph in placeholders_remaining:
                    if ph in system_prompt or ph in user_prompt:
                        print(f"  [WARN] Placeholder '{ph}' not replaced in L{level}")
                        failed += 1
            else:
                print(f"  [FAIL] L{level} prompt empty")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] L{level} error: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_validator_stats():
    """Test validation statistics tracking."""
    print("\n" + "=" * 60)
    print("TESTING VALIDATION STATS")
    print("=" * 60)
    
    validator = LeakageValidator()
    
    # Get rejection stats
    stats = validator.get_rejection_stats()
    print(f"  Total rejections logged: {stats['total_rejections']}")
    print(f"  Rejections by reason: {stats['by_reason']}")
    print(f"  Rejections by level: {stats['by_level']}")
    
    # Get recent rejections
    recent = validator.get_recent_rejections(limit=5)
    print(f"  Recent rejections: {len(recent)}")
    
    return True


def test_hint_flow_simulation():
    """Simulate a complete hint request flow."""
    print("\n" + "=" * 60)
    print("TESTING HINT FLOW SIMULATION")
    print("=" * 60)
    
    validator = LeakageValidator()
    builder = PromptBuilder()
    
    exercise = MockExercise(
        concept="while loop decrement",
        llm_context="Student is learning while loops with decrementing counter.",
        common_mistakes=["infinite loop from not decrementing", "wrong stopping condition"],
    )
    
    # Simulate L3 hint generation
    print("  Simulating L3 hint flow...")
    system_prompt, user_prompt = builder.build("hint_l3_v1", exercise)
    
    # Mock LLM response (would normally come from API)
    mock_llm_response = (
        "Think of the while loop like a countdown timer. "
        "You need to know when to start, when to stop, and what happens between. "
        "The condition checks 'is time > 0?' If yes, do something and subtract time. "
        "What condition should you check? What should happen each second?"
    )
    
    result = validator.check(mock_llm_response, exercise, level=3)
    
    if result.is_valid:
        print(f"  [PASS] L3 hint validated successfully")
        print(f"         Hint preview: {mock_llm_response[:80]}...")
    else:
        print(f"  [FAIL] L3 hint validation failed: {result.reason}")
        return False
    
    # Simulate L4 hint generation
    print("  Simulating L4 hint flow...")
    system_prompt, user_prompt = builder.build("hint_l4_v1", exercise)
    
    mock_llm_response_l4 = (
        "Here's a structured approach to solve this:\n\n"
        "1. Initialize a counter variable (e.g., n)\n"
        "2. Set up your while condition to check if counter > 0\n"
        "3. Inside the loop:\n"
        "   - Print or process the current value\n"
        "   - Update the counter (# this is crucial!)\n\n"
        "Common mistake: forgetting to update the counter, causing an infinite loop."
    )
    
    result = validator.check(mock_llm_response_l4, exercise, level=4)
    
    if result.is_valid:
        print(f"  [PASS] L4 hint validated successfully")
    else:
        print(f"  [FAIL] L4 hint validation failed: {result.reason}")
        return False
    
    return True


def test_leakage_patterns():
    """Test specific leakage patterns."""
    print("\n" + "=" * 60)
    print("TESTING LEAKAGE PATTERNS")
    print("=" * 60)
    
    validator = LeakageValidator()
    exercise = MockExercise("for loop with range", "Student is learning for loops")
    
    patterns = [
        ("Here's the solution: x, y = y, x", True, "inline solution"),
        ("The correct answer is to use a temp variable", True, "correct answer phrase"),
        ("Simply do: result = x; x = y; y = result", True, "simply + code"),
        ("Try this approach", True, "try this pattern"),
        ("Loop through the range from start to end value", False, "educational content"),
    ]
    
    passed = 0
    for text, should_fail, description in patterns:
        result = validator.check(text, exercise, level=1)
        if should_fail and not result.is_valid:
            print(f"  [PASS] Correctly caught: {description}")
            passed += 1
        elif not should_fail and result.is_valid:
            print(f"  [PASS] Correctly allowed: {description}")
            passed += 1
        else:
            print(f"  [FAIL] {description}: expected {'fail' if should_fail else 'pass'}, got {'fail' if not result.is_valid else 'pass'}")
    
    print(f"\nResults: {passed}/{len(patterns)} passed")
    return passed == len(patterns)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI TUTOR - LLM HINT SYSTEM TEST SUITE")
    print("=" * 60)
    
    results = []
    
    results.append(("Leakage Validator", test_leakage_validator()))
    results.append(("Prompt Builder", test_prompt_builder()))
    results.append(("Validation Stats", test_validator_stats()))
    results.append(("Hint Flow Simulation", test_hint_flow_simulation()))
    results.append(("Leakage Patterns", test_leakage_patterns()))
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED - Review output above")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
