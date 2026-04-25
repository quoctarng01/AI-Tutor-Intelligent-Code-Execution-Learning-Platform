from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(payload: LoginRequest) -> dict[str, str]:
    return {"message": f"Login scaffold for {payload.email}"}
