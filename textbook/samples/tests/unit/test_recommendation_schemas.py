# DeciTima samples │ 初出 Phase 12
"""作業単位 12-1: Algorithm Recommendation のスキーマ(純粋 Pydantic)。

テスト対象 / ドライバ / スタブ:
- 対象: `app.schemas.recommendation` の各 BaseModel(型定義のみ)
- ドライバ: このテスト関数
- スタブ不要 ── 対象が純粋なデータ定義で外部依存を呼ばないため
"""

from __future__ import annotations

from tests.fixtures.optimization import build_travel_problem

from app.schemas.recommendation import (
    AlgorithmRecommendation,
    LlmAlgorithmComment,
    LlmRecommendation,
    RecommendationResponse,
    RecommendRequest,
)


def test_recommend_request_wraps_an_optimization_problem() -> None:
    request = RecommendRequest(problem=build_travel_problem())
    assert request.problem.problem_type == "travel_planning"


def test_algorithm_recommendation_defaults_llm_fields_to_none() -> None:
    """rule のみ(LLM未呼び出し/失敗)の場合、llm_rank/llm_comment は省略できる。"""
    rec = AlgorithmRecommendation(
        name="knapsack_dp",
        family="optimization",
        implementation="handwritten",
        description="予算/時間を2次元ナップサックとして解く厳密DP。",
        is_rule_preferred=True,
    )
    assert rec.llm_rank is None
    assert rec.llm_comment is None
    assert rec.time_complexity is None


def test_recommendation_response_notes_default_to_empty_list() -> None:
    response = RecommendationResponse(
        problem_type="travel_planning",
        rule_preferred="knapsack_dp",
        recommendations=[],
    )
    assert response.notes == []


def test_llm_recommendation_holds_ranked_names_and_comments() -> None:
    llm = LlmRecommendation(
        ranked_names=["greedy", "knapsack_dp"],
        comments=[LlmAlgorithmComment(name="greedy", comment="必ず予算内に収まる")],
    )
    assert llm.ranked_names == ["greedy", "knapsack_dp"]
    assert llm.comments[0].name == "greedy"
