"""
Answer evaluation service.
Evaluates student code submissions against test cases.
"""

import asyncio
from backend.config import settings
from backend.services.secure_sandbox import run_tests as run_sandbox_tests


class AnswerEvaluator:
    """Evaluates student code submissions."""

    def __init__(self):
        self.judge0_url = settings.judge0_base_url
        self.judge0_api_key = settings.judge0_api_key
        self.use_sandbox = True  # Use secure sandbox by default

    async def evaluate(self, code: str, test_cases: list[dict]) -> dict:
        """
        Evaluate student code against test cases.

        Args:
            code: Python source code
            test_cases: List of dicts with 'input' and 'expected_output'

        Returns:
            dict with 'passed' (bool), 'total' (int), 'passed_count' (int),
            and 'results' (list of individual test results)
        """
        if self.use_sandbox:
            return await self._evaluate_with_sandbox(code, test_cases)
        elif self.judge0_api_key and self.judge0_api_key != "your_judge0_api_key_here":
            return await self._evaluate_with_judge0(code, test_cases)
        else:
            # Fallback to secure sandbox
            return await self._evaluate_with_sandbox(code, test_cases)

    async def _evaluate_with_sandbox(self, code: str, test_cases: list[dict]) -> dict:
        """Evaluate using secure local Python sandbox."""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, run_sandbox_tests, code, test_cases)

        passed_count = sum(1 for r in results if r["passed"])
        return {
            "passed": passed_count == len(test_cases),
            "total": len(test_cases),
            "passed_count": passed_count,
            "results": results,
        }

    async def _evaluate_with_judge0(self, code: str, test_cases: list[dict]) -> dict:
        """Evaluate using Judge0 API."""
        import base64
        import httpx

        headers = {
            "X-RapidAPI-Key": self.judge0_api_key,
            "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
            "Content-Type": "application/json",
        }

        async def run_single(tc: dict) -> dict:
            payload = {
                "language_id": 71,  # Python
                "source_code": base64.b64encode(code.encode()).decode(),
                "stdin": base64.b64encode(tc.get("input", "").encode()).decode(),
                "expected_output": base64.b64encode(tc.get("expected_output", "").encode()).decode(),
                "cpu_time_limit": 2,
                "memory_limit": 128000,
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.judge0_url}/submissions?base64_encoded=true&wait=true",
                    json=payload,
                    headers=headers,
                )
                result = response.json()
                status_id = result.get("status", {}).get("id", 0)
                return {
                    "passed": status_id == 3,  # Accepted
                    "actual_output": result.get("stdout", ""),
                    "expected_output": tc.get("expected_output", ""),
                    "status": result.get("status", {}).get("description", ""),
                }

        results = await asyncio.gather(*[run_single(tc) for tc in test_cases])
        passed_count = sum(1 for r in results if r["passed"])

        return {
            "passed": passed_count == len(test_cases),
            "total": len(test_cases),
            "passed_count": passed_count,
            "results": list(results),
        }


# Global evaluator instance
_evaluator = AnswerEvaluator()


async def evaluate_code(code: str, test_cases: list[dict]) -> dict:
    """Evaluate code with the global evaluator."""
    return await _evaluator.evaluate(code, test_cases)
