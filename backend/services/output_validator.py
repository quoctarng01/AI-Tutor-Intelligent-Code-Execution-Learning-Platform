"""
Answer Leakage Validator for LLM-Generated Hints.
Prevents solutions, code, and answer keywords from leaking to students.

This is a living component — all rejections are logged for thesis analysis.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# Comprehensive leakage patterns (pattern, name)
LEAKAGE_PATTERNS = [
    # Direct solution statements
    (r"\bhere'?s? (the|a|your) (solution|answer|code|fix)\b", "direct_solution_statement"),
    (r"\bthe (correct|right|full|complete) (answer|solution|code)\b", "correct_answer_statement"),
    (r"\bhere'?s (how|what|why)\b", "here_is_pattern"),
    (r"\byou (should|can|need to) (write|use|do)\s+`[^`]+`", "code_suggestion_inline"),
    (r"\byou (should|can|need to) (write|use|do)\s+\w+\s*\(", "function_call_suggestion"),
    
    # Python code patterns that give away solutions
    (r"def \w+\([^)]*\):[^\n]*\n\s+return", "complete_function_definition"),
    (r"while .+:.*\n\s+(\w+ [+\-*/]=|\w+ =)", "while_loop_solution"),
    (r"for \w+ in .+:[^\n]*\n\s+\w+\(", "for_loop_solution"),
    (r"if .+ == .+:[^\n]*\n\s+print", "if_statement_solution"),
    (r"print\([^)]*(solution|answer|correct)[^)]*\)", "print_with_solution"),
    
    # Assignment patterns
    (r"=\s*(def |for |while |if |print\()", "assignment_like_pattern"),
    
    # Keyword combinations that hint at solution
    (r"\b(solution|answer)\b.{0,30}(is|equals|==)\b", "solution_keyword_combination"),
    (r"(try|use|write)\s+this:\s*\n", "try_this_pattern"),
    (r"(just|simply|easily)\s+(do|use|write)", "minimization_language"),
]

# Level-specific forbidden patterns (pattern, name)
LEVEL_SPECIFIC_PATTERNS = {
    1: [
        (r"```python", "code_block_l1"),
        (r"def \w+", "function_def_l1"),
        (r"for .+ in ", "for_loop_l1"),
        (r"while .+:", "while_loop_l1"),
        (r"if .+:", "if_statement_l1"),
        (r"return ", "return_statement_l1"),
        (r"print\(", "print_function_l1"),
    ],
    2: [
        (r"```python", "code_block_l2"),
        (r"def \w+\([^)]*\):", "function_def_l2"),
        (r"for .+ in .+:\n\s+print", "for_loop_print_l2"),
        (r"while .+:\n\s+\w+", "while_loop_l2"),
        (r"return .+\(", "return_with_call_l2"),
        (r"\bfor \w+ in \w+\([^)]*\):", "for_loop_inline_l2"),
    ],
    3: [
        (r"```python", "code_block_l3"),
        (r"def \w+\([^)]*\):[^\n]*\n\s+return \w+\(", "complete_function_l3"),
        (r"for .+ in .+:\n\s+\w+\(", "for_loop_complete_l3"),
    ],
    4: [
        # L4 allows more structure but still no complete solution
        (r"```python", "code_block_l4"),
    ],
}

# Level-specific forbidden words (relaxed for L1/L2 to allow educational terms)
# Level-specific forbidden words (checked with word boundaries)
LEVEL_FORBIDDEN_WORDS = {
    1: ["answer", "solution", "def ", "return ", "print("],
    2: ["answer", "solution", "def ", "return "],
    3: ["solution", "correct answer"],
    4: ["complete solution", "full answer"],
}

# Minimum response lengths per level
MIN_LENGTHS = {1: 20, 2: 30, 3: 50, 4: 80}

# Validation log file path
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
VALIDATION_LOG = LOG_DIR / "hint_validation.log"


class ValidationResult:
    def __init__(self, is_valid: bool, reason: Optional[str] = None, details: Optional[dict] = None):
        self.is_valid = is_valid
        self.reason = reason
        self.details = details or {}
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "reason": self.reason,
            "details": self.details,
        }


class LeakageValidator:
    """
    Validates LLM-generated hints for answer leakage.
    
    Checks:
    1. Minimum length requirements
    2. Leakage pattern detection
    3. Level-specific code patterns
    4. Forbidden word usage
    5. Concept relevance
    """
    
    def __init__(self):
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """Create log directory if it doesn't exist."""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    def _log_rejection(self, text: str, reason: str, details: dict) -> None:
        """Log validation rejection for thesis analysis."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "text_length": len(text),
            "text_preview": text[:100],
            "details": details,
        }
        try:
            with open(VALIDATION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # Don't fail validation due to logging errors
    
    def check(self, text: str, exercise, level: int) -> ValidationResult:
        """
        Validate hint text for answer leakage.
        
        Args:
            text: The hint text to validate
            exercise: Exercise object with concept attribute
            level: Hint level (1-4)
        
        Returns:
            ValidationResult with is_valid, reason, and details
        """
        if not text or not text.strip():
            return ValidationResult(False, "empty_response", {"text": ""})
        
        text_stripped = text.strip()
        text_lower = text_stripped.lower()
        
        # 1. Check minimum length
        min_length = MIN_LENGTHS.get(level, 30)
        if len(text_stripped) < min_length:
            self._log_rejection(text, "response_too_short", {
                "level": level, "min_length": min_length, "actual_length": len(text_stripped)
            })
            return ValidationResult(False, "response_too_short", {
                "level": level, "min_length": min_length, "actual_length": len(text_stripped)
            })
        
        # 2. Check for leakage patterns
        for pattern, pattern_name in LEAKAGE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                self._log_rejection(text, f"leakage_detected: {pattern_name}", {
                    "level": level, "pattern": pattern_name
                })
                return ValidationResult(False, f"leakage_detected: {pattern_name}", {
                    "pattern": pattern_name, "level": level
                })
        
        # 3. Check level-specific patterns
        level_patterns = LEVEL_SPECIFIC_PATTERNS.get(level, [])
        for pattern, pattern_name in level_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                self._log_rejection(text, f"level_specific_violation: {pattern_name}", {
                    "level": level, "pattern": pattern_name
                })
                return ValidationResult(False, f"level_specific_violation: {pattern_name}", {
                    "pattern": pattern_name, "level": level
                })
        
        # 4. Check for forbidden words
        forbidden = LEVEL_FORBIDDEN_WORDS.get(level, [])
        found_forbidden = []
        for word in forbidden:
            if word.lower() in text_lower:
                found_forbidden.append(word)
        if found_forbidden:
            self._log_rejection(text, "forbidden_words", {
                "level": level, "forbidden_words": found_forbidden
            })
            return ValidationResult(False, "forbidden_words", {
                "forbidden_words": found_forbidden, "level": level
            })
        
        # 5. Check concept relevance (if exercise has concept)
        if hasattr(exercise, "concept") and exercise.concept:
            concept_words = exercise.concept.lower().split()
            # Check first 3-5 meaningful words from concept
            meaningful_words = [w for w in concept_words if len(w) > 3 and w not in ("with", "using", "from")]
            if meaningful_words:
                concept_referenced = any(word in text_lower for word in meaningful_words[:5])
                if not concept_referenced:
                    self._log_rejection(text, "irrelevant_response", {
                        "level": level, "concept": exercise.concept, "checked_words": meaningful_words[:5]
                    })
                    return ValidationResult(False, "irrelevant_response", {
                        "concept": exercise.concept, "level": level
                    })
        
        return ValidationResult(True, "ok", {"level": level})
    
    def get_recent_rejections(self, limit: int = 10) -> list[dict]:
        """Get recent validation rejections for analysis."""
        rejections = []
        try:
            if VALIDATION_LOG.exists():
                with open(VALIDATION_LOG, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-limit:]:
                        try:
                            rejections.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
        return list(reversed(rejections))
    
    def get_rejection_stats(self) -> dict:
        """Get statistics on validation rejections."""
        stats = {"total_rejections": 0, "by_reason": {}, "by_level": {}}
        try:
            if VALIDATION_LOG.exists():
                with open(VALIDATION_LOG, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            stats["total_rejections"] += 1
                            
                            reason = entry.get("reason", "unknown")
                            stats["by_reason"][reason] = stats["by_reason"].get(reason, 0) + 1
                            
                            level = entry.get("details", {}).get("level", "unknown")
                            stats["by_level"][str(level)] = stats["by_level"].get(str(level), 0) + 1
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
        return stats


# Backward compatibility alias
OutputValidator = LeakageValidator
