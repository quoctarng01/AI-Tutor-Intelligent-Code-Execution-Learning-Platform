import json
from datetime import datetime

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import HintLog

async def log_event(event_name: str, payload: dict) -> None:
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "event": event_name,
        "payload": payload,
    }
    print(json.dumps(entry))


async def log_hint(
    db: AsyncSession,
    session_id,
    exercise_id: str,
    level: int,
    prompt_version: str,
    prompt_rendered: str,
    llm_response: str,
    was_pre_authored: bool,
) -> None:
    await db.execute(
        insert(HintLog).values(
            session_id=session_id,
            exercise_id=exercise_id,
            hint_level=level,
            prompt_version=prompt_version,
            prompt_rendered=prompt_rendered,
            llm_response=llm_response,
            was_pre_authored=was_pre_authored,
        )
    )
    await db.commit()
