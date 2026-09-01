"""作業単位 3-3: BenchmarkRunRepository。

対象 = BenchmarkRunRepository(永続化のみ)。ドライバ = db_session(インメモリ SQLite)。
スタブ不要 ── SQLite セッションが実 Postgres の代役そのもの(Phase-1-5 の repository と同型)。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.benchmark import BenchmarkRunRepository


async def test_create_and_get_by_id(db_session: AsyncSession) -> None:
    user = User(email=f"{uuid.uuid4()}@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.flush()

    repo = BenchmarkRunRepository(db_session)
    row = await repo.create(
        user_id=user.id,
        problem_type="route_planning",
        payload={"problem": {}, "entries": [{"algorithm": {"name": "dijkstra"}}], "runs": 3},
    )
    await db_session.commit()

    fetched = await repo.get_by_id(row.id)
    assert fetched is not None
    assert fetched.user_id == user.id
    assert fetched.payload["runs"] == 3
    assert fetched.payload["entries"][0]["algorithm"]["name"] == "dijkstra"
