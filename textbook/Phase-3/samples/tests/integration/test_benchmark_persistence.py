"""作業単位 3-3: benchmark_runs の永続化(実 PostgreSQL)。

@pytest.mark.integration ── `docker compose up postgres` の上で
`uv run pytest -m integration` したときだけ走る(既定では除外。Phase-0-9.md §1.4)。
実 Postgres 上で JSONB カラムへの書き込み・読み出しと、モデルからのテーブル生成を確認する。
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import app.models  # noqa: F401  Base.metadata に登録
from app.core.database import Base, engine
from app.models.user import User
from app.repositories.benchmark import BenchmarkRunRepository

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def pg_session() -> AsyncGenerator[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_benchmark_run_jsonb_roundtrips_on_postgres(pg_session: AsyncSession) -> None:
    user = User(email="bench-pg@example.com", hashed_password="x")
    pg_session.add(user)
    await pg_session.flush()

    repo = BenchmarkRunRepository(pg_session)
    row = await repo.create(
        user_id=user.id,
        problem_type="route_planning",
        payload={
            "problem": {"problem_type": "route_planning"},
            "entries": [{"algorithm": {"name": "dijkstra"}, "elapsed_ms_median": 1.2}],
            "runs": 5,
        },
    )
    await pg_session.commit()

    fetched = await repo.get_by_id(row.id)
    assert fetched is not None
    assert fetched.payload["runs"] == 5
    assert fetched.payload["entries"][0]["elapsed_ms_median"] == 1.2
