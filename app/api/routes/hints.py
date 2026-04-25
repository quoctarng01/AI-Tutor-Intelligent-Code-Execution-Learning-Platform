from fastapi import APIRouter

router = APIRouter()


@router.get("/{exercise_id}")
async def get_hint(exercise_id: str) -> dict[str, str]:
    return {"exercise_id": exercise_id, "hint": "Think about edge cases first."}
