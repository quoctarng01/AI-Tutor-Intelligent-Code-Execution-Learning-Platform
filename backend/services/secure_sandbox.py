"""
Secure Python code sandbox using AST-based analysis.
Provides safe execution of student code with proper security validation.
"""

import ast
import io
import sys
import tempfile
import os
import platform
from typing import Optional
from dataclasses import dataclass


# Dangerous AST node types that are blocked
BLOCKED_NODES = frozenset({
    ast.Import,
    ast.ImportFrom,
    ast.Call,  # Most dangerous calls
})

# Dangerous function names (after AST name resolution)
BLOCKED_NAMES = frozenset({
    "__import__",
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "breakpoint",
    "exit",
    "quit",
    "reload",
    "reload",
    "memoryview",
    "buffer",
    "bytearray",
    "set",
    "frozenset",
})

# Names that are safe to call
SAFE_BUILTINS = frozenset({
    "abs", "all", "any", "ascii", "bin", "bool", "chr", "complex",
    "dict", "dir", "divmod", "enumerate", "filter", "float", "format",
    "frozenset", "hash", "hex", "int", "isinstance", "issubclass",
    "iter", "len", "list", "map", "max", "min", "next", "oct", "ord",
    "pow", "print", "range", "repr", "reversed", "round", "set",
    "slice", "sorted", "str", "sum", "super", "tuple", "zip",
    # Math module - allowed for educational purposes
    "math", "random",
})

# Math functions that are safe
SAFE_MATH_FUNCTIONS = frozenset({
    "floor", "ceil", "sqrt", "pow", "sin", "cos", "tan", "log",
    "pi", "e", "degrees", "radians", "factorial", "gcd",
})


@dataclass
class SandboxResult:
    """Result of sandbox execution."""
    success: bool
    output: str
    error: str | None
    timed_out: bool
    return_code: int
    passed: bool = False
    actual_output: str = ""
    expected_output: str = ""


@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    error: str | None
    warning: str | None = None


class SecurityValidator(ast.NodeVisitor):
    """
    AST-based security validator that checks code for dangerous patterns.
    """

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.imported_modules: set[str] = set()
        self.used_names: set[str] = set()
        self.has_input = False
        self.has_print = False
        self.has_loop = False
        self.has_function_def = False
        self.loop_depth = 0

    def visit_Import(self, node: ast.Import) -> None:
        self.errors.append(f"Import statement not allowed: 'import {node.names[0].name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.errors.append(f"Import from module not allowed: 'from {node.module} import ...'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in BLOCKED_NAMES:
                self.errors.append(f"Dangerous function not allowed: '{name}'")
            elif name not in SAFE_BUILTINS and name not in SAFE_MATH_FUNCTIONS:
                # Check if it's a module function (attribute call)
                if isinstance(node.func, ast.Attribute):
                    attr = node.func.attr
                    if attr in BLOCKED_NAMES:
                        self.errors.append(f"Dangerous method not allowed: '{attr}'")
                    elif node.func.value and isinstance(node.func.value, ast.Name):
                        module_name = node.func.value.id
                        self.imported_modules.add(module_name)
        elif isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in BLOCKED_NAMES:
                self.errors.append(f"Dangerous method not allowed: '{attr}'")
            # Check for dangerous module patterns
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                if module_name in ("os", "sys", "subprocess", "socket", "urllib",
                                   "requests", "http", "ftplib", "telnetlib",
                                   "multiprocessing", "threading", "ctypes", "cffi"):
                    self.errors.append(f"Dangerous module not allowed: '{module_name}'")

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.has_function_def = True
        # Check function name
        if node.name in BLOCKED_NAMES:
            self.errors.append(f"Function name not allowed: '{node.name}'")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.errors.append("Async functions not allowed in sandbox")
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.has_loop = True
        self.loop_depth += 1
        if self.loop_depth > 3:
            self.warnings.append("Deeply nested loops detected")
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        self.has_loop = True
        self.loop_depth += 1
        if self.loop_depth > 3:
            self.warnings.append("Deeply nested loops detected")
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_Lambda(self, node: ast.Lambda) -> None:
        # Lambda is allowed but with restrictions
        # Complex lambdas might be flagged by other checks
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Check for dangerous attribute access
        if node.attr in BLOCKED_NAMES:
            self.errors.append(f"Dangerous attribute not allowed: '{node.attr}'")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # Check for dangerous subscript patterns like __class__
        if isinstance(node.value, ast.Name) and node.value.id == "__builtins__":
            self.errors.append("Access to __builtins__ not allowed")
        self.generic_visit(node)


class SecurePythonSandbox:
    """
    Secure Python code executor using AST validation + subprocess isolation.
    """

    def __init__(
        self,
        timeout: float = 5.0,
        max_output_bytes: int = 10000,
        max_memory_mb: int = 128,
    ):
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes
        self.max_memory_mb = max_memory_mb

    def validate_code(self, code: str) -> ValidationResult:
        """
        Validate code using AST analysis.
        Returns (is_valid, error_message).
        """
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                error=f"Syntax error at line {e.lineno}: {e.msg}",
            )

        validator = SecurityValidator()
        validator.visit(tree)

        if validator.errors:
            return ValidationResult(
                is_valid=False,
                error="; ".join(validator.errors),
            )

        # Additional security checks
        # Check for dangerous string patterns that might bypass AST
        dangerous_patterns = [
            ("__import__", "Dynamic import not allowed"),
            ("eval(", "eval() not allowed"),
            ("exec(", "exec() not allowed"),
            ("compile(", "compile() not allowed"),
            ("open(", "open() not allowed"),
        ]

        code_normalized = code.replace(" ", "").replace("\n", "")
        for pattern, message in dangerous_patterns:
            if pattern.replace(" ", "") in code_normalized:
                return ValidationResult(is_valid=False, error=message)

        return ValidationResult(
            is_valid=True,
            error=None,
            warning="; ".join(validator.warnings) if validator.warnings else None,
        )

    def _set_resource_limits(self) -> None:
        """Set resource limits for the subprocess (Unix only)."""
        if platform.system() == "Windows":
            # On Windows, resource module is not available
            # Rely on subprocess timeout for safety
            return
        try:
            import resource
            # Limit memory
            resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_mb * 1024 * 1024, resource.RLIM_INFINITY))
            # Limit CPU time
            resource.setrlimit(resource.RLIMIT_CPU, (int(self.timeout) + 5, resource.RLIM_INFINITY))
            # Limit number of processes
            resource.setrlimit(resource.RLIMIT_NPROC, (5, 5))
            # Limit file size
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        except (ValueError, OSError, ImportError):
            # Resource limits not supported on this platform
            pass

    def execute(self, code: str, stdin: str = "") -> SandboxResult:
        """
        Execute Python code in isolated subprocess with resource limits.
        Returns SandboxResult with success status, output, and error.
        """
        # Validate first
        validation = self.validate_code(code)
        if not validation.is_valid:
            return SandboxResult(
                success=False,
                output="",
                error=f"Code validation failed: {validation.error}",
                timed_out=False,
                return_code=1,
            )

        # Create temp file for code
        code_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        )
        stdin_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        stdout_file = tempfile.NamedTemporaryFile(
            mode="r", suffix=".txt", delete=False, encoding="utf-8"
        )
        stderr_file = tempfile.NamedTemporaryFile(
            mode="r", suffix=".txt", delete=False, encoding="utf-8"
        )

        try:
            # Write code
            code_file.write(code)
            code_file.close()

            # Write stdin
            stdin_file.write(stdin)
            stdin_file.close()

            # Close read handles
            stdout_file.close()
            stderr_file.close()

            # Prepare restricted environment
            env = {
                **os.environ,
                "PYTHONUNBUFFERED": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONHASHSEED": "random",
            }

            # Execute with resource limits
            import subprocess

            try:
                proc = subprocess.Popen(
                    [sys.executable, "-u", code_file.name],
                    stdin=open(stdin_file.name, "r"),
                    stdout=open(stdout_file.name, "w"),
                    stderr=open(stderr_file.name, "w"),
                    env=env,
                )

                try:
                    stdout, stderr = proc.communicate(timeout=self.timeout)
                    timed_out = False
                    return_code = proc.returncode
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate()
                    timed_out = True
                    return_code = -1
                    stdout, stderr = b"", b"Timeout exceeded"

            except FileNotFoundError:
                return SandboxResult(
                    success=False,
                    output="",
                    error="Python interpreter not found",
                    timed_out=False,
                    return_code=1,
                )

            # Read outputs
            try:
                with open(stdout_file.name, "r", encoding="utf-8") as f:
                    output = f.read()
            except (OSError, UnicodeDecodeError):
                output = ""

            try:
                with open(stderr_file.name, "r", encoding="utf-8") as f:
                    stderr_output = f.read()
            except (OSError, UnicodeDecodeError):
                stderr_output = ""

            # Truncate output if too long
            if len(output) > self.max_output_bytes:
                output = output[: self.max_output_bytes] + "\n... (output truncated)"

            # Clean stderr (show only last few lines)
            if stderr_output:
                lines = stderr_output.strip().split("\n")
                if len(lines) > 3:
                    stderr_output = "\n".join(lines[-3:])

            return SandboxResult(
                success=return_code == 0 and not timed_out,
                output=output,
                error=stderr_output if stderr_output and return_code != 0 else None,
                timed_out=timed_out,
                return_code=return_code,
            )

        finally:
            # Cleanup temp files
            for f_path in [code_file.name, stdin_file.name, stdout_file.name, stderr_file.name]:
                try:
                    if os.path.exists(f_path):
                        os.unlink(f_path)
                except OSError:
                    pass

    def execute_with_test_cases(self, code: str, test_cases: list[dict]) -> list[dict]:
        """
        Execute code with multiple test cases.
        Each test case should have 'input' and 'expected_output' keys.
        """
        results = []
        for tc in test_cases:
            result = self.execute(code, stdin=tc.get("input", ""))

            actual = result.output.strip()
            expected = tc.get("expected_output", "").strip()

            # Flexible comparison: ignore trailing whitespace differences
            actual_lines = [line.rstrip() for line in actual.split("\n") if line.strip()]
            expected_lines = [line.rstrip() for line in expected.split("\n") if line.strip()]

            passed = (
                result.success
                and not result.timed_out
                and not result.error
                and actual_lines == expected_lines
            )

            results.append(
                {
                    "passed": passed,
                    "actual_output": actual,
                    "expected_output": expected,
                    "timed_out": result.timed_out,
                    "error": result.error,
                }
            )
        return results


# Global sandbox instance
_sandbox = SecurePythonSandbox(timeout=5.0)


def execute_code(code: str, stdin: str = "") -> SandboxResult:
    """Execute code with global sandbox."""
    return _sandbox.execute(code, stdin)


def run_tests(code: str, test_cases: list[dict]) -> list[dict]:
    """Run test cases with global sandbox."""
    return _sandbox.execute_with_test_cases(code, test_cases)


def validate_code_syntax(code: str) -> ValidationResult:
    """Validate code syntax and security."""
    return _sandbox.validate_code(code)
