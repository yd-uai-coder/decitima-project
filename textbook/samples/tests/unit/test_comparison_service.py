# DeciTima samples │ 初出 Phase 14
"""作業単位 14-5: `ComparisonService`。

テスト対象 / ドライバ / スタブ:
- 対象: `ComparisonService.compare`
- ドライバ: このテスト関数
- スタブ: `FakeRedis`(RateLimiter が使う incr/expire だけ)+ `FakeLLM`
  (`app.algorithms.llm.route_llm.get_gemini_llm` と `app.services.comparison.get_gemini_llm`
  をそれぞれ差し替える ── Phase 12/13 と同じ「呼び出し元モジュールの名前空間を monkeypatch
  する」形。前者は LLM Only 経路、後者はナレーション生成)。Algorithm 経路は実装済みの
  `select_strategy`(dijkstra)をそのまま使う ── フェイク不要(純粋・既存)。
"""

from __future__ import annotations

import uuid
from typing import cast

import pytest
from redis.asyncio import Redis
from tests.fixtures.fake_llm import FakeLLM
from tests.fixtures.fake_redis import FakeRedis
from tests.fixtures.optimization import build_route_problem

from app.algorithms.llm import route_llm
from app.domain.solutions.route_planner import RouteSolution
from app.schemas.comparison import ComparisonNarrative, ComparisonRequest
from app.services import comparison
from app.services.comparison import ComparisonService
from app.services.errors import RateLimitExceededError

_CORRECT = RouteSolution(
    path_node_ids=["A", "B", "D", "E"], path_edge_ids=["e_ab", "e_bd", "e_de"], total_weight=5
)
_LYING = RouteSolution(
    path_node_ids=["A", "B", "D", "E"], path_edge_ids=["e_ab", "e_bd", "e_de"], total_weight=100
)

_NARRATIVE = ComparisonNarrative(
    summary="Algorithm の方が安定して valid でした",
    constraint_compliance_note="Algorithm 100% / LLM 66%",
    optimality_note="LLM は Algorithm と同等の経路も出せています",
    reproducibility_note="LLM は2種類の構造を返しました",
    verifiability_note="LLM の出力も同じ検証器に通しています",
)


def _service() -> ComparisonService:
    return ComparisonService(cast(Redis, FakeRedis()))


def _patch_llm_only(monkeypatch: pytest.MonkeyPatch, structured=None, sequence=None) -> None:
    monkeypatch.setattr(
        route_llm,
        "get_gemini_llm",
        lambda **_: FakeLLM(structured=structured, structured_sequence=sequence),
    )


def _patch_narrative(monkeypatch: pytest.MonkeyPatch, structured: ComparisonNarrative) -> None:
    monkeypatch.setattr(comparison, "get_gemini_llm", lambda **_: FakeLLM(structured=structured))


async def test_compare_all_llm_runs_match_algorithm(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_llm_only(monkeypatch, structured=_CORRECT)
    _patch_narrative(monkeypatch, _NARRATIVE)

    result = await _service().compare(
        user_id=uuid.uuid4(),
        request=ComparisonRequest(problem=build_route_problem(), llm_runs=3),
    )

    assert result.algorithm_used.name == "dijkstra"
    assert result.algorithm_result.status == "valid"
    assert len(result.llm_results) == 3
    assert all(r.status == "valid" for r in result.llm_results)
    assert result.metrics.constraint_compliance_rate_algorithm == 1.0
    assert result.metrics.constraint_compliance_rate_llm == 1.0
    assert result.metrics.reproducibility_distinct_solutions_llm == 1
    assert result.metrics.error_rate_llm == 0.0
    assert result.metrics.optimality_avg_quality_ratio_llm == pytest.approx(1.0)
    assert result.narrative is not None
    assert result.narrative.summary == _NARRATIVE.summary


async def test_compare_mixed_valid_and_lying_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """3回中2回は正しい解、1回は total_weight を偽った解 ── 構造検証がそれを invalid にし、
    制約遵守率・再現性の両方に反映される。"""
    _patch_llm_only(monkeypatch, sequence=[_CORRECT, _LYING, _CORRECT])
    _patch_narrative(monkeypatch, _NARRATIVE)

    result = await _service().compare(
        user_id=uuid.uuid4(),
        request=ComparisonRequest(problem=build_route_problem(), llm_runs=3),
    )

    statuses = [r.status for r in result.llm_results]
    assert statuses == ["valid", "invalid", "valid"]
    assert result.metrics.constraint_compliance_rate_llm == pytest.approx(2 / 3)
    # 構造が違う(total_weight が違う)ので2種類とカウントされる(妥当性とは独立の指標)
    assert result.metrics.reproducibility_distinct_solutions_llm == 2


async def test_compare_counts_llm_exceptions_as_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_llm_only(monkeypatch, sequence=[_CORRECT, RuntimeError("LLM timed out")])
    _patch_narrative(monkeypatch, _NARRATIVE)

    result = await _service().compare(
        user_id=uuid.uuid4(),
        request=ComparisonRequest(problem=build_route_problem(), llm_runs=2),
    )

    assert result.llm_results[0].error is None
    assert result.llm_results[1].error is not None
    assert result.llm_results[1].status is None
    assert result.metrics.error_rate_llm == pytest.approx(0.5)
    # エラーになった回は成功件数の分母から除く(1/1 = 100%)
    assert result.metrics.constraint_compliance_rate_llm == 1.0


async def test_compare_falls_back_to_mechanical_narrative_when_llm_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_only(monkeypatch, structured=_CORRECT)

    class _BoomLLM:
        def with_structured_output(self, _schema: object) -> _BoomLLM:
            return self

        async def ainvoke(self, _messages: object) -> None:
            raise RuntimeError("narrative LLM unavailable")

    monkeypatch.setattr(comparison, "get_gemini_llm", lambda **_: _BoomLLM())

    result = await _service().compare(
        user_id=uuid.uuid4(),
        request=ComparisonRequest(problem=build_route_problem(), llm_runs=1),
    )

    assert result.narrative is not None
    assert "ナレーション生成に失敗した" in result.narrative.summary


async def test_compare_enforces_its_own_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(comparison.settings, "COMPARE_RATE_LIMIT_PER_HOUR", 1)
    _patch_llm_only(monkeypatch, structured=_CORRECT)
    _patch_narrative(monkeypatch, _NARRATIVE)
    service = _service()
    user_id = uuid.uuid4()
    request = ComparisonRequest(problem=build_route_problem(), llm_runs=1)

    await service.compare(user_id=user_id, request=request)
    with pytest.raises(RateLimitExceededError):
        await service.compare(user_id=user_id, request=request)
