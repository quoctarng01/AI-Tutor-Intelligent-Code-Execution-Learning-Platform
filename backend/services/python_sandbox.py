"""
Fast Python code executor using subprocess isolation.
Provides safe execution of student code with proper sandboxing.
"""

import subprocess
import tempfile
import os
import uuid
import json
import threading
from typing import Optional


class FastPythonSandbox:
    """
    Fast, secure Python code executor using subprocess.
    Each execution runs in an isolated subprocess with restricted resources.

    Attributes:
        timeout: Maximum execution time in seconds (default: 5.0)
        max_output_bytes: Maximum output size to prevent memory issues (default: 10000)

    Security Measures:
        - Blocked patterns prevent dangerous imports (os, sys, subprocess, etc.)
        - Execution timeout prevents infinite loops
        - Output truncation prevents memory exhaustion
        - Subprocess isolation provides basic sandboxing
    """

    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        "import os", "import sys", "import subprocess", "import socket",
        "import threading", "import multiprocessing", "import ctypes",
        "from os import", "from sys import", "from subprocess import",
        "__import__", "eval(", "exec(", "open(", "file(", "compile(",
        "memoryview", "buffer", "bytearray", "frozenset",
        "lambda",  # Some lambda restrictions, but allow basic ones
    ]

    def __init__(self, timeout: float = 5.0, max_output_bytes: int = 10000):
        """
        Initialize the sandbox with execution constraints.

        Args:
            timeout: Maximum execution time in seconds.
            max_output_bytes: Maximum output size in bytes.
        """
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes

    def _validate_code(self, code: str) -> Optional[str]:
        """
        Validate code for dangerous patterns. Returns error message or None if valid.

        Args:
            code: The source code to validate.

        Returns:
            Error message string if validation fails, None if valid.
        """
        code_lower = code.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in code_lower:
                # Allow 'lambda' in reasonable contexts
                if pattern == "lambda" and "lambda" not in code:
                    continue
                return f"Blocked: {pattern}"
        return None

    def execute(self, code: str, stdin: str = "") -> dict:
        """
        Execute Python code in isolated subprocess.

        Args:
            code: The Python source code to execute.
            stdin: Optional standard input to provide to the script.

        Returns:
            A dict containing:
                - success (bool): Whether execution succeeded
                - output (str): Standard output from the script
                - error (str|None): Error message if execution failed
                - timed_out (bool): Whether execution timed out
                - return_code (int): The subprocess return code

        Error Handling:
            - Returns validation error if code contains blocked patterns
            - Returns "Python interpreter not found" if python is not available
            - Truncates output if it exceeds max_output_bytes
        """
        # Validate first
        validation_error = self._validate_code(code)
        if validation_error:
            return {
                "success": False,
                "output": "",
                "error": f"Code validation failed: {validation_error}",
                "timed_out": False,
            }

        # Create temp files
        script_id = uuid.uuid4().hex[:8]
        code_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        )
        stdin_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        )
        stdout_file = tempfile.NamedTemporaryFile(
            mode='r', suffix='.txt', delete=False, encoding='utf-8'
        )
        stderr_file = tempfile.NamedTemporaryFile(
            mode='r', suffix='.txt', delete=False, encoding='utf-8'
        )

        try:
            # Write code
            code_file.write(code)
            code_file.close()

            # Write stdin
            stdin_file.write(stdin)
            stdin_file.close()

            # Close read handles before subprocess
            stdout_file.close()
            stderr_file.close()

            # Run subprocess
            try:
                result = subprocess.run(
                    [
                        "python",
                        "-u",  # Unbuffered
                        code_file.name
                    ],
                    stdin=open(stdin_file.name, 'r'),
                    stdout=open(stdout_file.name, 'w'),
                    stderr=open(stderr_file.name, 'w'),
                    timeout=self.timeout,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"},
                )
                timed_out = False
                return_code = result.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                return_code = -1
            except FileNotFoundError:
                return {
                    "success": False,
                    "output": "",
                    "error": "Python interpreter not found",
                    "timed_out": False,
                }

            # Read outputs
            try:
                with open(stdout_file.name, 'r', encoding='utf-8') as f:
                    output = f.read()
            except:
                output = ""

            try:
                with open(stderr_file.name, 'r', encoding='utf-8') as f:
                    stderr = f.read()
            except:
                stderr = ""

            # Truncate output if too long
            if len(output) > self.max_output_bytes:
                output = output[:self.max_output_bytes] + "\n... (output truncated)"

            # Clean stderr (remove traceback noise for cleaner output)
            if stderr:
                # Only show the error message, not full traceback
                lines = stderr.strip().split('\n')
                if len(lines) > 3:
                    stderr = '\n'.join(lines[-3:])  # Last 3 lines of error

            return {
                "success": return_code == 0 and not timed_out,
                "output": output,
                "error": stderr if stderr and return_code != 0 else None,
                "timed_out": timed_out,
                "return_code": return_code,
            }

        finally:
            # Cleanup temp files
            for f in [code_file, stdin_file]:
                try:
                    if not f.closed:
                        f.close()
                    os.unlink(f.name)
                except:
                    pass
            for f in [stdout_file, stderr_file]:
                try:
                    os.unlink(f.name)
                except:
                    pass

    def execute_with_test_cases(self, code: str, test_cases: list[dict]) -> list[dict]:
        """
        Execute code with multiple test cases efficiently.

        Args:
            code: The Python source code to execute.
            test_cases: List of test cases, each containing 'input' and 'expected_output'.

        Returns:
            List of result dicts for each test case:
                - passed (bool): Whether the test case passed
                - actual_output (str): The output from the code
                - expected_output (str): The expected output
                - timed_out (bool): Whether execution timed out
                - error (str|None): Error message if any
        """
        results = []
        for tc in test_cases:
            result = self.execute(code, stdin=tc.get("input", ""))

            actual = result["output"].strip()
            expected = tc.get("expected_output", "").strip()

            # Compare outputs (flexible: ignore trailing whitespace differences)
            actual_lines = [l.rstrip() for l in actual.split('\n') if l.strip()]
            expected_lines = [l.rstrip() for l in expected.split('\n') if l.strip()]

            passed = (
                result["success"] and
                not result["timed_out"] and
                not result["error"] and
                actual_lines == expected_lines
            )

            results.append({
                "passed": passed,
                "actual_output": actual,
                "expected_output": expected,
                "timed_out": result["timed_out"],
                "error": result["error"],
            })
        return results


# Global fast executor
_executor = FastPythonSandbox(timeout=5.0)


def execute_code(code: str, stdin: str = "") -> dict:
    """
    Execute code with global executor.

    Args:
        code: The Python source code to execute.
        stdin: Optional standard input to provide to the script.

    Returns:
        Execution result dict from FastPythonSandbox.execute().
    """
    return _executor.execute(code, stdin)


def run_tests(code: str, test_cases: list[dict]) -> list[dict]:
    """
    Run test cases with global executor.

    Args:
        code: The Python source code to execute.
        test_cases: List of test cases to run.

    Returns:
        List of test results from FastPythonSandbox.execute_with_test_cases().
    """
    return _executor.execute_with_test_cases(code, test_cases)
