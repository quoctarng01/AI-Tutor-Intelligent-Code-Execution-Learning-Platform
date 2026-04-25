# Backend Services

from backend.services.hint_engine import HintEngine, MAX_HINT_LEVEL
from backend.services.llm_client import LLMClient, get_llm_client, LLMError, LLMServiceError
from backend.services.output_validator import LeakageValidator, ValidationResult
from backend.services.answer_evaluator import evaluate_code, AnswerEvaluator
from backend.services.secure_sandbox import (
    SecurePythonSandbox,
    execute_code,
    run_tests,
    validate_code_syntax,
    SandboxResult,
    ValidationResult as SandboxValidationResult,
)
from backend.services.prompt_builder import PromptBuilder
from backend.services.logger import log_event, log_hint
from backend.services.logging_service import (
    configure_logging,
    get_logger,
    get_request_id,
    get_session_id,
    logger as app_logger,
)
from backend.services.rate_limiter import (
    RateLimiter,
    get_rate_limiter,
    limiter as rate_limiter_instance,
)
from backend.services.cache_service import (
    CacheService,
    get_cache_service,
    cached_get,
    cached_set,
    cached_delete,
)
from backend.services.metrics import (
    get_metrics_collector,
    MetricsCollector,
    track_llm_metrics,
    track_code_execution,
    get_metrics,
)

__all__ = [
    # Hint Engine
    "HintEngine",
    "MAX_HINT_LEVEL",
    # LLM Client
    "LLMClient",
    "get_llm_client",
    "LLMError",
    "LLMServiceError",
    # Output Validator
    "LeakageValidator",
    "ValidationResult",
    # Answer Evaluator
    "evaluate_code",
    "AnswerEvaluator",
    # Secure Sandbox
    "SecurePythonSandbox",
    "execute_code",
    "run_tests",
    "validate_code_syntax",
    "SandboxResult",
    "SandboxValidationResult",
    # Prompt Builder
    "PromptBuilder",
    # Logger
    "log_event",
    "log_hint",
    # Logging Service
    "configure_logging",
    "get_logger",
    "get_request_id",
    "get_session_id",
    "app_logger",
    # Rate Limiter
    "RateLimiter",
    "get_rate_limiter",
    "rate_limiter_instance",
    # Cache Service
    "CacheService",
    "get_cache_service",
    "cached_get",
    "cached_set",
    "cached_delete",
    # Metrics
    "get_metrics_collector",
    "MetricsCollector",
    "track_llm_metrics",
    "track_code_execution",
    "get_metrics",
]
