# DeciTima samples │ Phase 1 │ 改訂 Phase 13
"""GET /api/v1/solutions/{id} / GET /api/v1/problems/{id} /
GET /api/v1/problems/{id}/solutions ── 永続化された問題・解の取得。
POST /api/v1/solutions/{id}/explain ── (Phase 13-3) 保存済みの解を自然言語で説明する。

設計は Phase-0-7.md §2。所有者スコープ(他ユーザーのものは 404)。
`explain` は同じ「solutions」という操作対象なので、新しいファイルを作らずこのファイルに追加する
(algorithms.py に recommend を足した Phase 12 と同じ判断)。
"""

import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, RedisDep, SessionDep  # (Phase 13-3) RedisDep は explain 用
from app.schemas.explanation import ExplanationResponse  # (Phase 13-3)
from app.schemas.optimization import ProblemRead, SolutionRead
from app.services.explanation import SolutionExplanationService  # (Phase 13-3)
from app.services.optimization_read import OptimizationReadService

router = APIRouter(tags=["solutions"])


@router.get("/solutions/{solution_id}", response_model=SolutionRead)
async def get_solution(
    solution_id: uuid.UUID, session: SessionDep, current_user: CurrentUserDep
) -> SolutionRead:
    """保存済みの解 1 件を返す。"""
    row = await OptimizationReadService(session).get_solution(solution_id, user_id=current_user.id)
    return SolutionRead.model_validate(row)


@router.get("/problems/{problem_id}", response_model=ProblemRead)
async def get_problem(
    problem_id: uuid.UUID, session: SessionDep, current_user: CurrentUserDep
) -> ProblemRead:
    """保存済みの問題 1 件を返す。"""
    row = await OptimizationReadService(session).get_problem(problem_id, user_id=current_user.id)
    return ProblemRead.model_validate(row)


@router.get("/problems/{problem_id}/solutions", response_model=list[SolutionRead])
async def list_problem_solutions(
    problem_id: uuid.UUID, session: SessionDep, current_user: CurrentUserDep
) -> list[SolutionRead]:
    """ある問題に対する全解(複数アルゴリズム分。本格利用は Phase 3)。"""
    rows = await OptimizationReadService(session).list_solutions_for_problem(
        problem_id, user_id=current_user.id
    )
    return [SolutionRead.model_validate(r) for r in rows]


# (Phase 13-3)
@router.post("/solutions/{solution_id}/explain", response_model=ExplanationResponse)
async def explain_solution(
    solution_id: uuid.UUID, session: SessionDep, current_user: CurrentUserDep, redis: RedisDep
) -> ExplanationResponse:
    """保存済みの解を自然言語で説明する(LLM、補助機能。永続化しない)。
    README §13「なぜこの解か / どの制約が重要か / どのアルゴリズムか / 他候補との違い /
    改善余地」を返す。"""
    service = SolutionExplanationService(session, redis)
    return await service.explain(
        solution_id,
        user_id=current_user.id,
        bypass_rate_limit=current_user.is_superuser,
    )
