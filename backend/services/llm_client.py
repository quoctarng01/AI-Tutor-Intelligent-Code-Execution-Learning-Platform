"""
Groq API client with proper error handling and retry logic.
"""

from typing import Any

import httpx

from backend.config import settings
from backend.exceptions import LLMServiceError
from backend.services.logging_service import get_logger


logger = get_logger("llm_client")


class LLMError(Exception):
    """Base error for LLM operations."""

    def __init__(self, message: str, code: str = "LLM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class LLMValidationError(LLMError):
    """LLM response validation error."""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class LLMTimeoutError(LLMError):
    """LLM request timeout error."""

    def __init__(self, message: str = "LLM request timed out"):
        super().__init__(message, "TIMEOUT")


class LLMClient:
    """Groq-powered LLM client wrapper with proper error handling."""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = "llama-3.3-70b-versatile"
        self.base_url = "https://api.groq.com/openai/v1"
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
        retries: int = 2,
    ) -> str:
        """
        Generate a completion using Groq API.

        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt/query
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            retries: Number of retry attempts

        Returns:
            The LLM's response text

        Raises:
            LLMError: If the API call fails after all retries
        """
        if not self.api_key or self.api_key in ("your_openai_api_key_here", ""):
            logger.warning("llm_no_api_key", message="Using mock response - no API key configured")
            return await self._mock_complete(system_prompt, user_prompt)

        return await self._call_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            retries=retries,
        )

    async def _call_api(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        retries: int,
    ) -> str:
        """Make Groq API call with retry logic."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("retry-after", 60))
                        if attempt < retries:
                            logger.warning(
                                "llm_rate_limited",
                                attempt=attempt,
                                retry_after=retry_after,
                            )
                            import asyncio
                            await asyncio.sleep(retry_after)
                            continue
                        raise LLMError(
                            f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                            "RATE_LIMITED",
                        )

                    # Handle authentication errors
                    if response.status_code == 401:
                        raise LLMError(
                            "Invalid API key. Please check your configuration.",
                            "AUTH_ERROR",
                        )

                    response.raise_for_status()
                    data = response.json()

                    if "choices" not in data or not data["choices"]:
                        raise LLMValidationError("Empty response from LLM")

                    content = data["choices"][0]["message"]["content"]
                    if not content or not content.strip():
                        raise LLMValidationError("Empty content in LLM response")

                    logger.debug(
                        "llm_response_received",
                        tokens=len(content.split()),
                        model=self.model,
                    )
                    return content

            except httpx.TimeoutException as e:
                last_error = LLMTimeoutError(f"Request timed out: {e}")
                logger.warning("llm_timeout", attempt=attempt, error=str(e))

            except httpx.HTTPStatusError as e:
                last_error = LLMError(
                    f"HTTP error {e.response.status_code}: {e.response.text[:200]}",
                    f"HTTP_{e.response.status_code}",
                )
                logger.warning("llm_http_error", attempt=attempt, error=str(e))

            except (LLMError, LLMValidationError, LLMTimeoutError):
                raise

            except Exception as e:
                last_error = LLMError(f"Unexpected error: {str(e)}", "UNKNOWN")
                logger.error("llm_unexpected_error", attempt=attempt, error=str(e))

            # Retry on recoverable errors
            if attempt < retries:
                import asyncio
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue

        # All retries exhausted
        error_msg = f"Groq API call failed after {retries + 1} attempts"
        if last_error:
            error_msg += f": {last_error}"
        logger.error("llm_all_retries_failed", error=error_msg)
        raise LLMServiceError(error_msg)

    async def _mock_complete(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Mock response when no API key is configured."""
        return (
            f"[Mock LLM Response]\n\n"
            f"This is a placeholder response. Add your Groq API key to enable real AI hints.\n\n"
            f"Hint level: Extracted from system prompt context\n"
            f"Concept: Based on the exercise being attempted"
        )


# Singleton instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
