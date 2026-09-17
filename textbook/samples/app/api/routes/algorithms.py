# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 12
"""GET /api/v1/algorithms ── registry に登録されたアルゴリズムの一覧。
POST /api/v1/algorithms/recommend ── (Phase 12) 候補アルゴリズムと推薦理由を返す。

設計は Phase-0-7.md §2 / §3.3。認証必須(MVP は統一。公開が必要になったら緩める)。
`recommend` は同じ「algorithms」という操作対象なので、新しいファイルを作らずこのファイルに
追加する(CLAUDE.md「操作(エンドポイント群)で割る」の既存判断に合わせる)。
"""

from collections import defaultdict

from fastapi import APIRouter

from app.algorithms.registry import all_strategies
from app.api.deps import CurrentUserDep, RedisDep  # (Phase 12) RedisDep は recommend 用
from app.schemas.optimization import AlgorithmInfo, AlgorithmListResponse
from app.schemas.recommendation import RecommendationResponse, RecommendRequest  # (Phase 12)
from app.services.algorithm_recommendation import AlgorithmRecommendationService  # (Phase 12)

router = APIRouter(prefix="/algorithms", tags=["algorithms"])


@router.get("", response_model=AlgorithmListResponse)
async def list_algorithms(_current_user: CurrentUserDep) -> AlgorithmListResponse:
    """(name, implementation) ごとに、登録されている problem_type をまとめて返す。"""
    # (name, implementation) をキーに problem_type を集約する
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    meta_by_key: dict[tuple[str, str], AlgorithmInfo] = {}
    for problem_type, strategy in all_strategies():
        key = (strategy.meta.name, strategy.meta.implementation)
        grouped[key].add(problem_type)
        meta_by_key[key] = AlgorithmInfo(
            name=strategy.meta.name,
            family=strategy.meta.family,
            implementation=strategy.meta.implementation,
            problem_types=[],
            time_complexity=strategy.meta.time_complexity,
        )

    algorithms = [
        info.model_copy(update={"problem_types": sorted(grouped[key])})
        for key, info in meta_by_key.items()
    ]
    return AlgorithmListResponse(algorithms=algorithms)


# (Phase 12)
@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_algorithm(
    payload: RecommendRequest,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> RecommendationResponse:
    """構造化済み問題に対し、候補アルゴリズムと推薦理由(ルール + LLM)を返す。
    /solve の既定選択には影響しない ── 呼び出し側が確認のうえで ?algorithm= に明示指定する
    想定(README「LLM単独では最終決定しない」)。"""
    service = AlgorithmRecommendationService(redis)
    return await service.recommend(
        user_id=current_user.id,
        problem=payload.problem,
        bypass_rate_limit=current_user.is_superuser,
    )
