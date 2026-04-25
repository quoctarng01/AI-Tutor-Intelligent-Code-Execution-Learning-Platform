from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_exercises() -> list[dict[str, str]]:
    return [{"id": "ex-1", "title": "Sample Exercise"}]
