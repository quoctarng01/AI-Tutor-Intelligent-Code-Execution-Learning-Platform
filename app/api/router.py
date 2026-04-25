from fastapi import APIRouter

from app.api.routes import auth, exercises, submit

# Import backend hints router for LLM hint generation
try:
    import backend.routers.hints as backend_hints
    hints_router = backend_hints.router
except ImportError:
    # Fallback placeholder if backend not available
    hints_router = APIRouter()

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(hints_router, prefix="/hints", tags=["hints"])
api_router.include_router(submit.router, prefix="/submit", tags=["submit"])
