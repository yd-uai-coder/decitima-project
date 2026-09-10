# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 5,7
"""共通スキーマの中核(アグリゲータ)。

- Objective / ConstraintBase(+ 判別子付きサブタイプ)/ GenericConstraint / AnyConstraint
- ProblemData(problem_type を判別子にした判別可能ユニオン)
- OptimizationProblem

LLM と Algorithm Engine の間に置く「共通言語」。LLM の出力を構造化してアルゴリズムに渡すことで、
アルゴリズムを差し替えても動作が保証され、複数アルゴリズムに同じデータを渡して比較できる。

Phase 5-3 での変更: `ProblemData` / `OptimizationProblem.problem_type` に `network_design` を追加。
Phase 7-3 での変更: 同様に `travel_planning` を追加(`Phase-0-2.md` §8.1)。
既存の problem_type のコードには一切触れない ── ハイブリッドスキーマの狙い。
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.problems.network_design import NetworkDesignData
from app.domain.problems.route_planner import RouteData
from app.domain.problems.shift_scheduler import ShiftData
from app.domain.problems.travel_planner import TravelData  # (Phase 7-3)

# ---------------------------------------------------------------------------
# 目的(Objective)
# ---------------------------------------------------------------------------


class Objective(BaseModel):
    """最適化の目的を1つ表す。何を、どちら方向に良くしたいか。"""

    sense: Literal["minimize", "maximize"]
    target: str  # 対象メトリクスの名前。計算方法はアルゴリズム側が解釈する
    weight: float = 1.0  # 多目的のときの相対的な重み。単一目的なら 1.0
    description: str | None = None


# ---------------------------------------------------------------------------
# 制約(Constraint)── 基底は共通フィールドだけ。判別子 kind は各サブタイプが宣言する
# (基底に kind: str を置くと pyright standard が reportIncompatibleVariableOverride を出す)
# ---------------------------------------------------------------------------


class ConstraintBase(BaseModel):
    """全サブタイプ共通のフィールドだけ。"""

    severity: Literal["hard", "soft"] = "hard"  # hard=絶対 / soft=破れるがペナルティ
    penalty: float | None = None  # soft を1件破るごとに目的関数へ加算
    description: str | None = None


class NumericBoundConstraint(ConstraintBase):
    """ある数値フィールドの上限・下限・等値を課す宣言的な制約。"""

    kind: Literal["numeric_bound"] = "numeric_bound"
    field: str  # 対象フィールド名(例: "total_weight")
    operator: Literal["<=", ">=", "==", "<", ">"]
    value: float


class RequiredInclusionConstraint(ConstraintBase):
    """解に必ず含めなければならない要素を列挙する制約(必須経由ノード / 必須リンク等)。"""

    kind: Literal["required_inclusion"] = "required_inclusion"
    items: list[str]


class ForbiddenConstraint(ConstraintBase):
    """解に含めてはならない要素を列挙する制約(通行禁止エッジ / 使えないリンク等)。"""

    kind: Literal["forbidden"] = "forbidden"
    items: list[str]


class StaffingConstraint(ConstraintBase):
    """各スロットの必要人数を満たすことを要求する制約(詳細は data 側が持つ)。"""

    kind: Literal["staffing"] = "staffing"


class GenericConstraint(ConstraintBase):
    """専用サブタイプのない ad-hoc な制約。kind は任意の文字列。"""

    kind: str


type AnyConstraint = Annotated[
    NumericBoundConstraint
    | RequiredInclusionConstraint
    | ForbiddenConstraint
    | StaffingConstraint
    | GenericConstraint,
    Field(union_mode="left_to_right"),
]

# ---------------------------------------------------------------------------
# 問題定義(OptimizationProblem)
# ---------------------------------------------------------------------------

# problem_type を判別子にした判別可能ユニオン。新しい問題タイプはここに 1 項目足すだけ。
type ProblemData = Annotated[
    RouteData | ShiftData | NetworkDesignData | TravelData,  # (Phase 7-3) TravelData
    Field(discriminator="problem_type"),
]


class OptimizationProblem(BaseModel):
    """LLM と Algorithm Engine の共通言語。目的・制約・問題固有データを束ねる。"""

    problem_type: Literal[
        "route_planning", "shift_scheduling", "network_design", "travel_planning"
    ]  # (Phase 7-3) travel_planning
    objectives: list[Objective]
    constraints: list[AnyConstraint] = Field(default_factory=list)
    data: ProblemData
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _problem_type_matches_data(self) -> OptimizationProblem:
        """トップの problem_type と data.problem_type の不一致を早期に弾く(Input Validation)。"""
        if self.problem_type != self.data.problem_type:
            raise ValueError(
                f"problem_type={self.problem_type!r} does not match "
                f"data.problem_type={self.data.problem_type!r}"
            )
        return self
