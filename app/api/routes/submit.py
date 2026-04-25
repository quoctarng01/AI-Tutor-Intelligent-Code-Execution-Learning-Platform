from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SubmissionRequest(BaseModel):
    exercise_id: str
    answer: str


@router.post("/")
async def submit_answer(payload: SubmissionRequest) -> dict[str, str]:
    return {"exercise_id": payload.exercise_id, "result": "received"}
