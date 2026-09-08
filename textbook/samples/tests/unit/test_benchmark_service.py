# DeciTima samples │ 初出 Phase 3 │ 改訂 Phase 4,5
"""作業単位 3-3 / 3-4(Phase 4/5 で登録 strategy が増えた現行版)。

対象 = BenchmarkService(オーケストレーション)。ドライバ = このテスト関数 + db_session。
スタブ = FakeRedis のみ。ProblemValidationService / SolutionVerificationService / 各 strategy /
measure_call はすべて本物(純粋)。

Phase 4/5 の変更: route_planning に bellman_ford / a_star / networkx(dijkstra 名)が加わり、
network_design に kruskal / prim / networkx が加わった ── entry 数の期待値を更新。
"""

import uuid
from typing import cast

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from tests.fixtures.fake_redis import FakeRedis
from tests.fixtures.optimization import build_network_problem, build_route_problem

from app.models.optimization import BenchmarkRun
from app.models.user import User
from app.schemas.optimization import BenchmarkRequest
from app.services.benchmark import BenchmarkService
from app.services.errors import (
    InfeasibleProblemError,
    NoAlgorithmError,
    ProblemValidationError,
)

# route_planning の手実装トラック(networkx は name="dijkstra" で重なる)
_ROUTE_HANDWRITTEN = {"dijkstra", "bellman_ford", "a_star", "brute_force"}


def _service(session: AsyncSession) -> BenchmarkService:
    return BenchmarkService(session, cast(Redis, FakeRedis()))


async def _make_user(session: AsyncSession) -> User:
    user = User(email=f"{uuid.uuid4()}@example.com", hashed_password="x")
    session.add(user)
    await session.flush()
    return user


async def test_benchmarks_all_route_strategies(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    outcome = await _service(db_session).run(
        user_id=user.id,
        request=BenchmarkRequest(problem=build_route_problem(), runs=2, persist=False),
    )
    assert {e.algorithm.name for e in outcome.entries} == _ROUTE_HANDWRITTEN
    # 手実装トラックは _ops を出す。ライブラリトラックは出さない。
    for e in outcome.entries:
        assert e.solution_status == "valid"
        assert e.elapsed_ms_median >= 0.0
        assert e.peak_memory_kb > 0.0
        if e.algorithm.implementation == "handwritten":
            assert e.operation_count is not None and e.operation_count > 0
        else:
            assert e.operation_count is None


async def test_benchmarks_network_design_strategies(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    outcome = await _service(db_session).run(
        user_id=user.id,
        request=BenchmarkRequest(problem=build_network_problem(), runs=1, persist=False),
    )
    assert {e.algorithm.name for e in outcome.entries} == {"kruskal", "prim"}
    assert all(e.metrics["total_weight"] == 10.0 for e in outcome.entries)


async def test_algorithms_filter_matches_both_dijkstra_implementations(
    db_session: AsyncSession,
) -> None:
    user = await _make_user(db_session)
    outcome = await _service(db_session).run(
        user_id=user.id,
        request=BenchmarkRequest(
            problem=build_route_problem(),
            algorithms=["dijkstra"],
            runs=1,
            persist=False,
        ),
    )
    assert [e.algorithm.name for e in outcome.entries] == ["dijkstra", "dijkstra"]
    assert {e.algorithm.implementation for e in outcome.entries} == {
        "handwritten",
        "library:networkx",
    }


async def test_unknown_algorithm_name_raises(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    with pytest.raises(NoAlgorithmError):
        await _service(db_session).run(
            user_id=user.id,
            request=BenchmarkRequest(
                problem=build_route_problem(),
                algorithms=["nope"],
                runs=1,
                persist=False,
            ),
        )


async def test_invalid_problem_raises_before_measuring(
    db_session: AsyncSession,
) -> None:
    user = await _make_user(db_session)
    with pytest.raises(InfeasibleProblemError):
        await _service(db_session).run(
            user_id=user.id,
            request=BenchmarkRequest(
                problem=build_route_problem(forbidden=["e_ce", "e_de"]),
                runs=1,
                persist=False,
            ),
        )


async def test_unknown_start_node_raises(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    with pytest.raises(ProblemValidationError):
        await _service(db_session).run(
            user_id=user.id,
            request=BenchmarkRequest(problem=build_route_problem(start="Z"), runs=1, persist=False),
        )


async def test_quality_ratio_is_one_when_all_optimal(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    outcome = await _service(db_session).run(
        user_id=user.id,
        request=BenchmarkRequest(problem=build_route_problem(), runs=1, persist=False),
    )
    assert all(e.quality_ratio == 1.0 for e in outcome.entries)


async def test_persist_creates_benchmark_run_row(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    outcome = await _service(db_session).run(
        user_id=user.id,
        request=BenchmarkRequest(problem=build_route_problem(), runs=1, persist=True),
    )
    assert outcome.benchmark_id is not None
    row = await db_session.get(BenchmarkRun, outcome.benchmark_id)
    assert row is not None
    assert row.problem_type == "route_planning"
    assert row.payload["runs"] == 1
    # route_planning: dijkstra(手) + bellman_ford + a_star + dijkstra(networkx) + brute_force = 5
    assert len(row.payload["entries"]) == 5


async def test_persist_false_returns_no_id(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    outcome = await _service(db_session).run(
        user_id=user.id,
        request=BenchmarkRequest(problem=build_route_problem(), runs=1, persist=False),
    )
    assert outcome.benchmark_id is None
