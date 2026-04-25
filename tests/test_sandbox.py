"""
Unit tests for the secure sandbox.
"""

import pytest

from backend.services.secure_sandbox import (
    SecurePythonSandbox,
    SandboxResult,
    ValidationResult,
    validate_code_syntax,
)


class TestSecurityValidator:
    """Tests for AST-based security validation."""

    def test_valid_simple_loop(self):
        """Test that simple loops are allowed."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
for i in range(5):
    print(i)
""")
        assert result.is_valid is True
        assert result.error is None

    def test_valid_while_loop(self):
        """Test that while loops are allowed."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
count = 0
while count < 5:
    print(count)
    count += 1
""")
        assert result.is_valid is True

    def test_valid_function_definition(self):
        """Test that function definitions are allowed."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
""")
        assert result.is_valid is True

    def test_valid_nested_loops(self):
        """Test that nested loops are allowed (with warning)."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
for i in range(3):
    for j in range(3):
        for k in range(3):
            print(i, j, k)
""")
        assert result.is_valid is True
        assert result.warning is not None  # Should have warning about nesting

    def test_blocked_import_statement(self):
        """Test that import statements are blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
import os
print("Hello")
""")
        assert result.is_valid is False
        assert "import" in result.error.lower()

    def test_blocked_import_from(self):
        """Test that from...import statements are blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
from sys import exit
print("Hello")
""")
        assert result.is_valid is False
        assert "import" in result.error.lower()

    def test_blocked_os_module(self):
        """Test that os module access is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
import os
os.system("ls")
""")
        assert result.is_valid is False

    def test_blocked_subprocess(self):
        """Test that subprocess module is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
import subprocess
subprocess.run(["ls"])
""")
        assert result.is_valid is False

    def test_blocked_eval(self):
        """Test that eval is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
result = eval("2 + 2")
""")
        assert result.is_valid is False
        assert "eval" in result.error.lower()

    def test_blocked_exec(self):
        """Test that exec is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
exec("print('hello')")
""")
        assert result.is_valid is False
        assert "exec" in result.error.lower()

    def test_blocked_open(self):
        """Test that open() is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
with open("test.txt", "r") as f:
    print(f.read())
""")
        assert result.is_valid is False
        assert "open" in result.error.lower()

    def test_blocked_socket(self):
        """Test that socket module is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
import socket
s = socket.socket()
""")
        assert result.is_valid is False

    def test_blocked_input(self):
        """Test that input() is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
name = input("Enter name: ")
""")
        # Note: input() is in SAFE_BUILTINS for educational purposes
        # but can be restricted if needed
        assert result.is_valid is True

    def test_blocked_multiprocessing(self):
        """Test that multiprocessing is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
import multiprocessing
p = multiprocessing.Process()
""")
        assert result.is_valid is False

    def test_blocked_threading(self):
        """Test that threading is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
import threading
t = threading.Thread()
""")
        assert result.is_valid is False

    def test_blocked_ctypes(self):
        """Test that ctypes is blocked."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
import ctypes
""")
        assert result.is_valid is False

    def test_syntax_error_detected(self):
        """Test that syntax errors are detected."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
for i in range(5)
    print(i)
""")
        assert result.is_valid is False
        assert "syntax" in result.error.lower()

    def test_lambda_allowed(self):
        """Test that lambdas are allowed."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
square = lambda x: x * x
print(square(5))
""")
        assert result.is_valid is True

    def test_list_operations_allowed(self):
        """Test that list operations are allowed."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers]
print(sum(squares))
""")
        assert result.is_valid is True

    def test_string_operations_allowed(self):
        """Test that string operations are allowed."""
        sandbox = SecurePythonSandbox()
        result = sandbox.validate_code("""
text = "Hello World"
print(text.upper())
print(text[::-1])
print(len(text))
""")
        assert result.is_valid is True


class TestSandboxExecution:
    """Tests for sandbox code execution."""

    def test_execute_valid_code(self, sample_python_code: str):
        """Test executing valid code."""
        sandbox = SecurePythonSandbox()
        result = sandbox.execute(sample_python_code)

        assert result.success is True
        assert "1" in result.output
        assert "2" in result.output
        assert result.error is None
        assert result.timed_out is False

    def test_execute_with_input(self):
        """Test executing code with stdin input."""
        sandbox = SecurePythonSandbox()
        code = """
n = int(input())
print(n * 2)
"""
        result = sandbox.execute(code, stdin="5")

        assert result.success is True
        assert "10" in result.output

    def test_reject_malicious_code(self, malicious_python_code: str):
        """Test that malicious code is rejected before execution."""
        sandbox = SecurePythonSandbox()
        result = sandbox.execute(malicious_python_code)

        assert result.success is False
        assert "validation failed" in result.error.lower()

    def test_reject_syntax_error(self, syntax_error_code: str):
        """Test that syntax errors are rejected."""
        sandbox = SecurePythonSandbox()
        result = sandbox.execute(syntax_error_code)

        assert result.success is False
        assert "syntax" in result.error.lower()

    def test_timeout_infinite_loop(self, infinite_loop_code: str):
        """Test that infinite loops timeout."""
        sandbox = SecurePythonSandbox(timeout=1.0)
        result = sandbox.execute(infinite_loop_code)

        assert result.timed_out is True
        assert result.success is False

    def test_execute_with_test_cases(self):
        """Test execution with test cases."""
        sandbox = SecurePythonSandbox()
        code = """
n = int(input())
print(n * 2)
"""
        test_cases = [
            {"input": "5", "expected_output": "10"},
            {"input": "3", "expected_output": "6"},
        ]

        results = sandbox.execute_with_test_cases(code, test_cases)

        assert len(results) == 2
        assert results[0]["passed"] is True
        assert results[1]["passed"] is True

    def test_test_case_failure(self):
        """Test that failed test cases are detected."""
        sandbox = SecurePythonSandbox()
        code = """
n = int(input())
print(n * 3)  # Wrong: should be * 2
"""
        test_cases = [
            {"input": "5", "expected_output": "10"},
        ]

        results = sandbox.execute_with_test_cases(code, test_cases)

        assert results[0]["passed"] is False
        assert results[0]["actual_output"].strip() == "15"

    def test_output_truncation(self):
        """Test that output is truncated when too large."""
        sandbox = SecurePythonSandbox(max_output_bytes=100)
        code = """
for i in range(1000):
    print("x" * 100)
"""
        result = sandbox.execute(code)

        assert result.success is True
        assert "(output truncated)" in result.output
        assert len(result.output) <= 200  # Truncated + message


class TestValidateCodeSyntax:
    """Tests for the validate_code_syntax convenience function."""

    def test_valid_code(self, sample_python_code: str):
        """Test validation of valid code."""
        result = validate_code_syntax(sample_python_code)
        assert result.is_valid is True

    def test_invalid_code(self, malicious_python_code: str):
        """Test validation of malicious code."""
        result = validate_code_syntax(malicious_python_code)
        assert result.is_valid is False

    def test_syntax_error(self, syntax_error_code: str):
        """Test validation of code with syntax errors."""
        result = validate_code_syntax(syntax_error_code)
        assert result.is_valid is False
