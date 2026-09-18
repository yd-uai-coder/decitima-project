# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 5,7,8,9,14
"""解の中核(アグリゲータ)。

- AlgorithmMeta / ConstraintViolation
- SolutionData(problem_type を判別子にした判別可能ユニオン)
- CandidateSolution

Phase 5-3 で SolutionData に NetworkDesignSolution を、Phase 7-3 で TravelSolution を、
Phase 8-3 で ProjectSolution を、Phase 9-1 で LogisticsSolution を追加(`Phase-0-2.md` §8.1)。

Phase 14-1 で `AlgorithmMeta.family` に `"llm"` を追加した(進行のルール #12。実在の消費者は
`app/algorithms/llm/` の `LlmOnly*Strategy` 6 本 ── README §14「LLM vs Algorithm Comparison」)。
これらは本番 `REGISTRY` には登録しないが、`AlgorithmStrategy` Protocol を満たす他の戦略と
契約上は完全に同格であることを型でも表す(6つ目の「app/algorithms/ サブパッケージ」として
`app/algorithms/llm/` を新設した)。
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from app.domain.solutions.logistics import LogisticsSolution  # (Phase 9-1)
from app.domain.solutions.network_design import NetworkDesignSolution
from app.domain.solutions.project_manager import ProjectSolution  # (Phase 8-3)
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.shift_scheduler import ShiftSolution
from app.domain.solutions.travel_planner import TravelSolution  # (Phase 7-3)

# AlgorithmMeta.family は app/algorithms/ のサブパッケージと 1 対 1
# (Phase 1〜9)
# type AlgorithmFamily = Literal["search", "graph", "optimization", "scheduling", "patterns"]
# (Phase 14-1) "llm"(app/algorithms/llm/)を追加。REGISTRY には登録しない比較専用の戦略だが、
# 契約(AlgorithmStrategy)上は他の family と同格であることを型で表す。
type AlgorithmFamily = Literal["search", "graph", "optimization", "scheduling", "patterns", "llm"]

# 解の状態
type SolutionStatus = Literal["valid", "invalid", "infeasible"]


class ConstraintViolation(BaseModel):
    """検証で見つかった制約違反1件。どの制約を、どう破ったか。"""

    constraint_kind: str
    severity: Literal["hard", "soft"]
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class AlgorithmMeta(BaseModel):
    """解を生成したアルゴリズムの素性。比較可能性(NFR-3)の土台になる。"""

    name: str
    family: AlgorithmFamily  # (Phase 14-1) 直接 Literal を書いていた箇所を型エイリアス参照に統一
    # implementation: "handwritten" / "library:networkx" / "library:ortools" / "llm" など
    implementation: str
    time_complexity: str | None = None
    space_complexity: str | None = None


# problem_type 判別子付きの判別可能ユニオン。新しい問題タイプはここに 1 項目足すだけ。
type SolutionData = Annotated[
    RouteSolution
    | ShiftSolution
    | NetworkDesignSolution
    | TravelSolution
    | ProjectSolution
    | LogisticsSolution,  # (Phase 9-1)
    Field(discriminator="problem_type"),
]


class CandidateSolution(BaseModel):
    """アルゴリズムが返す候補解。検証結果と生成元アルゴリズムを必ず伴う。"""

    # problem_ref: 永続化時は Problem の id。単発実行では None
    problem_ref: uuid.UUID | None = None
    status: Literal["valid", "invalid", "infeasible"]
    assignments: SolutionData
    # metrics: 目的の実測値。例 {"total_weight": 9} / {"labor_cost": 21500}
    metrics: dict[str, float] = Field(default_factory=dict)
    violations: list[ConstraintViolation] = Field(default_factory=list)
    produced_by: AlgorithmMeta
