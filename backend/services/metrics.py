"""
Prometheus metrics for monitoring AI Tutor performance and costs.
"""

import time
from typing import Callable
from functools import wraps
from contextlib import contextmanager

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)

from backend.services.logging_service import get_logger


logger = get_logger("metrics")


# Application info
APP_INFO = Info(
    "ai_tutor",
    "AI Tutor application information",
)
APP_INFO.info({
    "version": "1.0.0",
    "service": "ai-tutor-api",
})


# Request metrics
REQUEST_COUNT = Counter(
    "ai_tutor_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "ai_tutor_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REQUEST_IN_PROGRESS = Gauge(
    "ai_tutor_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)


# LLM metrics
LLM_REQUESTS = Counter(
    "ai_tutor_llm_requests_total",
    "Total number of LLM API requests",
    ["status", "model"],
)

LLM_LATENCY = Histogram(
    "ai_tutor_llm_request_duration_seconds",
    "LLM API request latency in seconds",
    ["model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)

LLM_TOKENS = Counter(
    "ai_tutor_llm_tokens_total",
    "Total number of LLM tokens processed",
    ["model", "type"],  # type: prompt, completion
)

LLM_COST = Counter(
    "ai_tutor_llm_cost_dollars",
    "Estimated LLM API cost in dollars",
    ["model"],
)

LLM_ERRORS = Counter(
    "ai_tutor_llm_errors_total",
    "Total number of LLM errors",
    ["error_type", "model"],
)


# Code execution metrics
CODE_EXECUTIONS = Counter(
    "ai_tutor_code_executions_total",
    "Total number of code executions",
    ["status"],  # success, timeout, error, rejected
)

CODE_EXECUTION_LATENCY = Histogram(
    "ai_tutor_code_execution_duration_seconds",
    "Code execution latency in seconds",
    ["sandbox_type"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

SANDBOX_VALIDATION_FAILURES = Counter(
    "ai_tutor_sandbox_validation_failures_total",
    "Total number of sandbox validation failures",
    ["reason"],  # syntax_error, dangerous_code, timeout
)


# Hint system metrics
HINTS_REQUESTED = Counter(
    "ai_tutor_hints_requested_total",
    "Total number of hints requested",
    ["level", "source"],  # source: pre_authored, llm
)

HINTS_VALIDATION_FAILURES = Counter(
    "ai_tutor_hints_validation_failures_total",
    "Total number of hint validation failures",
    ["level", "reason"],
)

LLM_HINTS_CACHED = Counter(
    "ai_tutor_llm_hints_cached_total",
    "Total number of LLM hints served from cache",
)


# Exercise metrics
EXERCISES_ATTEMPTED = Counter(
    "ai_tutor_exercises_attempted_total",
    "Total number of exercise attempts",
    ["exercise_id", "topic"],
)

EXERCISES_COMPLETED = Counter(
    "ai_tutor_exercises_completed_total",
    "Total number of exercises completed",
    ["exercise_id", "topic"],
)

EXERCISES_FIRST_ATTEMPT = Counter(
    "ai_tutor_exercises_first_attempt_total",
    "Total number of exercises solved on first attempt",
    ["exercise_id", "topic"],
)


# Session metrics
ACTIVE_SESSIONS = Gauge(
    "ai_tutor_active_sessions",
    "Number of currently active sessions",
    ["group_type"],  # tutor, control
)

SESSIONS_CREATED = Counter(
    "ai_tutor_sessions_created_total",
    "Total number of sessions created",
    ["group_type"],
)


# Rate limiting metrics
RATE_LIMIT_HITS = Counter(
    "ai_tutor_rate_limit_hits_total",
    "Total number of rate limit hits",
    ["endpoint", "limit_type"],
)


# Database metrics
DB_QUERY_COUNT = Counter(
    "ai_tutor_db_queries_total",
    "Total number of database queries",
    ["operation", "table"],
)

DB_QUERY_LATENCY = Histogram(
    "ai_tutor_db_query_duration_seconds",
    "Database query latency in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)


# Token estimates for cost calculation (based on Groq pricing)
TOKEN_COST_PER_1K = {
    "llama-3.3-70b-versatile": {
        "prompt": 0.0,  # Free tier
        "completion": 0.0,
    },
    "llama-3.1-8b-instant": {
        "prompt": 0.0,
        "completion": 0.0,
    },
}


class MetricsCollector:
    """
    Collects and records application metrics.
    """

    def __init__(self):
        self._start_time = time.time()

    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
    ) -> None:
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    def increment_request_in_progress(self, method: str, endpoint: str) -> None:
        """Increment requests in progress gauge."""
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

    def decrement_request_in_progress(self, method: str, endpoint: str) -> None:
        """Decrement requests in progress gauge."""
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

    def record_llm_request(
        self,
        model: str,
        status: str,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """Record LLM API request metrics."""
        LLM_REQUESTS.labels(status=status, model=model).inc()
        LLM_LATENCY.labels(model=model).observe(duration)

        if prompt_tokens > 0:
            LLM_TOKENS.labels(model=model, type="prompt").inc(prompt_tokens)
        if completion_tokens > 0:
            LLM_TOKENS.labels(model=model, type="completion").inc(completion_tokens)

        # Estimate cost
        if model in TOKEN_COST_PER_1K:
            cost_info = TOKEN_COST_PER_1K[model]
            total_tokens = prompt_tokens + completion_tokens
            cost = (total_tokens / 1000) * (cost_info["prompt"] + cost_info["completion"])
            if cost > 0:
                LLM_COST.labels(model=model).inc(cost)

    def record_llm_error(self, model: str, error_type: str) -> None:
        """Record LLM error."""
        LLM_ERRORS.labels(error_type=error_type, model=model).inc()

    def record_code_execution(
        self,
        status: str,
        duration: float,
        sandbox_type: str = "secure_sandbox",
    ) -> None:
        """Record code execution metrics."""
        CODE_EXECUTIONS.labels(status=status).inc()
        CODE_EXECUTION_LATENCY.labels(sandbox_type=sandbox_type).observe(duration)

    def record_sandbox_validation_failure(self, reason: str) -> None:
        """Record sandbox validation failure."""
        SANDBOX_VALIDATION_FAILURES.labels(reason=reason).inc()

    def record_hint_request(self, level: int, source: str) -> None:
        """Record hint request."""
        HINTS_REQUESTED.labels(level=str(level), source=source).inc()

    def record_hint_validation_failure(self, level: int, reason: str) -> None:
        """Record hint validation failure."""
        HINTS_VALIDATION_FAILURES.labels(level=str(level), reason=reason).inc()

    def record_cached_hint(self) -> None:
        """Record cached LLM hint."""
        LLM_HINTS_CACHED.inc()

    def record_exercise_attempt(self, exercise_id: str, topic: str) -> None:
        """Record exercise attempt."""
        EXERCISES_ATTEMPTED.labels(exercise_id=exercise_id, topic=topic).inc()

    def record_exercise_completed(self, exercise_id: str, topic: str) -> None:
        """Record exercise completion."""
        EXERCISES_COMPLETED.labels(exercise_id=exercise_id, topic=topic).inc()

    def record_first_attempt_success(self, exercise_id: str, topic: str) -> None:
        """Record first attempt success."""
        EXERCISES_FIRST_ATTEMPT.labels(exercise_id=exercise_id, topic=topic).inc()

    def set_active_sessions(self, count: int, group_type: str) -> None:
        """Set active sessions gauge."""
        ACTIVE_SESSIONS.labels(group_type=group_type).set(count)

    def increment_sessions_created(self, group_type: str) -> None:
        """Increment sessions created counter."""
        SESSIONS_CREATED.labels(group_type=group_type).inc()

    def record_rate_limit_hit(self, endpoint: str, limit_type: str) -> None:
        """Record rate limit hit."""
        RATE_LIMIT_HITS.labels(endpoint=endpoint, limit_type=limit_type).inc()

    def record_db_query(self, operation: str, table: str, duration: float) -> None:
        """Record database query."""
        DB_QUERY_COUNT.labels(operation=operation, table=table).inc()
        DB_QUERY_LATENCY.labels(operation=operation, table=table).observe(duration)


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


@contextmanager
def track_request_metrics(method: str, endpoint: str):
    """Context manager to track HTTP request metrics."""
    collector = get_metrics_collector()
    collector.increment_request_in_progress(method, endpoint)
    start_time = time.time()

    try:
        yield
    finally:
        duration = time.time() - start_time
        collector.decrement_request_in_progress(method, endpoint)
        # Status will be set by the actual response


def track_llm_metrics(model: str):
    """Decorator to track LLM request metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                collector.record_llm_error(model, type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                collector.record_llm_request(
                    model=model,
                    status=status,
                    duration=duration,
                )

        return wrapper
    return decorator


def track_code_execution(sandbox_type: str = "secure_sandbox"):
    """Decorator to track code execution metrics."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except TimeoutError:
                status = "timeout"
                raise
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector.record_code_execution(
                    status=status,
                    duration=duration,
                    sandbox_type=sandbox_type,
                )

        return wrapper
    return decorator


def get_metrics() -> tuple[bytes, str]:
    """Get Prometheus metrics in the appropriate format."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
