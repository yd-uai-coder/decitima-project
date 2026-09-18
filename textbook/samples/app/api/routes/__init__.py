# DeciTima samples │ 初出 Phase 1 │ 改訂 2,3,9,10,11,14
from fastapi import APIRouter

from app.api.routes.algorithms import router as algorithms_router
from app.api.routes.auth import router as auth_router
from app.api.routes.benchmark import router as benchmark_router
from app.api.routes.comparison import router as comparison_router  # (Phase 14-6)
from app.api.routes.jobs import router as jobs_router  # (Phase 9-8)
from app.api.routes.simulate import router as simulate_router  # (Phase 10-4)
from app.api.routes.solutions import router as solutions_router
from app.api.routes.solve import router as solve_router
from app.api.routes.structure import router as structure_router  # (Phase 11-7)
from app.api.routes.users import router as users_router
from app.api.routes.verify import router as verify_router

# 各機能別ルーターを1つのAPIRouterに集約し、main.pyから一括でincludeできるようにする。
# (Phase 1) chat_router（app/api/routes/chat.py）はDeciTimaではPhase 11まで無効化していた。
# (Phase 11-7) Web検索QA機能を廃止し、DeciTima用の structure_router に置き換えた。
# chat.py・app/services/chat.py・app/schemas/chat.py の ChatRequest/ChatResponse・
# app/ai/tools/tavily.py・app/schemas/generation.py は削除する(手順は Phase-11-7.md)。
api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(solve_router)
api_router.include_router(jobs_router)  # (Phase 9-8) 既存の同期 solve_router と併存
api_router.include_router(simulate_router)  # (Phase 10-4) jobs_router と同じ Job テーブルを再利用
api_router.include_router(structure_router)  # (Phase 11-7)
api_router.include_router(algorithms_router)
api_router.include_router(solutions_router)
api_router.include_router(verify_router)
api_router.include_router(benchmark_router)
api_router.include_router(comparison_router)  # (Phase 14-6)
