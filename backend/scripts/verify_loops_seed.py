import asyncio
import sys

from sqlalchemy import inspect, select

from backend.database import SessionLocal, engine
from backend.models import Exercise

EXPECTED_LOOPS_COUNT = 5


async def verify_exercises_seed() -> int:
    async with engine.connect() as conn:
        table_exists = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table("exercises"))

    if not table_exists:
        print("ERROR: 'exercises' table does not exist.")
        return 1

    async with SessionLocal() as session:
        result = await session.execute(
            select(Exercise.id, Exercise.title).where(Exercise.topic == "loops").order_by(Exercise.id)
        )
        rows = result.all()

    if len(rows) != EXPECTED_LOOPS_COUNT:
        print(
            f"ERROR: Expected {EXPECTED_LOOPS_COUNT} seeded 'loops' exercises, found {len(rows)}."
        )
        if rows:
            print("Found:")
            for exercise_id, title in rows:
                print(f"- {exercise_id}: {title}")
        return 1

    print("OK: 'exercises' table exists and has 5 seeded 'loops' exercises.")
    print("Seeded loops exercises:")
    for exercise_id, title in rows:
        print(f"- {exercise_id}: {title}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(verify_exercises_seed()))
