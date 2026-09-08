# DeciTima samples │ Phase 1
"""作業単位 1-5: Problem / Solution の永続化(実 PostgreSQL)。

@pytest.mark.integration ── `docker compose up postgres` の上で
`uv run pytest -m integration` したときだけ走る(既定では除外。Phase-0-9.md §1.4)。
実 Postgres 上で JSONB カラムへの書き込み・読み出しと、モデルからのテーブル生成を確認する。

このファイルは実 PG が必要なため、教材生成セッションでは未実行
(tests/integration/conftest.py の client パターンに揃えて記述)。
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.fixtures.optimization import build_route_problem

import app.models  # noqa: F401  Base.metadata に Problem/Solution を登録
from app.core.database import Base, engine
from app.models.user import User
from app.repositories.optimization import ProblemRepository, SolutionRepository

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def pg_session() -> AsyncGenerator[AsyncSession]:
    """実 Postgres に対して、毎回まっさらなスキーマで非同期セッションを提供する。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_jsonb_payload_roundtrips_on_postgres(pg_session: AsyncSession) -> None:
    user = User(email="pg@example.com", hashed_password="x")
    pg_session.add(user)
    await pg_session.flush()

    problem = build_route_problem(forbidden=["e_bd"], required=["C"])
    prow = await ProblemRepository(pg_session).create(
        user_id=user.id,
        problem_type=problem.problem_type,
        payload=problem.model_dump(mode="json"),
    )
    srow = await SolutionRepository(pg_session).create(
        problem_id=prow.id,
        status="valid",
        algorithm_name="dijkstra",
        algorithm_implementation="handwritten",
        payload={"status": "valid", "metrics": {"total_weight": 9.0}},
    )
    await pg_session.commit()

    fetched = await SolutionRepository(pg_session).get_by_id(srow.id)
    assert fetched is not None
    assert fetched.payload["metrics"]["total_weight"] == 9.0

    # JSONB はまるごと代入で更新(部分ミューテーションは追跡されない)
    fetched.payload = {**fetched.payload, "status": "invalid"}
    await pg_session.commit()
    again = await SolutionRepository(pg_session).get_by_id(srow.id)
    assert again is not None
    assert again.payload["status"] == "invalid"
