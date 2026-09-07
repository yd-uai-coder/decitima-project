"""共通スキーマの中核(アグリゲータ)。

- Objective / ConstraintBase(+ 判別子付きサブタイプ)/ GenericConstraint / AnyConstraint
- ProblemData(problem_type を判別子にした判別可能ユニオン)
- OptimizationProblem

葉モジュール(route_planner.py / shift_scheduler.py)を「絶対 import」で束ねる。
逆方向(葉 → このファイル)の依存は無いので循環しない(Phase-0-2.md §2.5)。

Phase 1 のユニオンは route / shift の 2 メンバー。network_design(MST)は Phase 5 で
1 行足す(§「拡張ポイント」/ Phase-0-2.md §8.1)。
"""

# [以降 Phase で修正予定 ── Phase 5-3] このファイルの現行版はこのまま(スナップショット)。
# Phase 5-3 で ProblemData / OptimizationProblem.problem_type に network_design を追加(判別可能ユニオンを 3 メンバーに)。
# 現行版 textbook/Phase-4/samples/app/domain/problems/problem.py。

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.problems.route_planner import RouteData
from app.domain.problems.shift_scheduler import ShiftData

# ---------------------------------------------------------------------------
# 目的(Objective)
# ---------------------------------------------------------------------------


class Objective(BaseModel):
    """最適化の目的を1つ表す。何を、どちら方向に良くしたいか。"""

    sense: Literal["minimize", "maximize"]  # 最小化 or 最大化
    target: str  # 対象メトリクスの名前。計算方法はアルゴリズム側が解釈する
    weight: float = 1.0  # 多目的のときの相対的な重み。単一目的なら 1.0 のまま
    description: str | None = None


# ---------------------------------------------------------------------------
# 制約(Constraint)
# ---------------------------------------------------------------------------


class ConstraintBase(BaseModel):
    """全サブタイプ共通のフィールドだけを持つ基底。

    判別子 kind は基底に置かず各サブタイプが宣言する。基底に kind: str を置いて
    サブクラスで Literal に狭めると pyright standard が reportIncompatibleVariableOverride
    を出すため(Phase-0-2.md §4.2)。
    """

    severity: Literal["hard", "soft"] = "hard"  # hard=絶対に破れない / soft=破れるがペナルティ
    penalty: float | None = None  # soft 制約を1件破るごとに目的関数へ加算するペナルティ
    description: str | None = None


class NumericBoundConstraint(ConstraintBase):
    """ある数値フィールドの上限・下限・等値を課す宣言的な制約。"""

    kind: Literal["numeric_bound"] = "numeric_bound"
    field: str  # 対象フィールド名(例: "total_weight" / "labor_cost")
    operator: Literal["<=", ">=", "==", "<", ">"]
    value: float


class RequiredInclusionConstraint(ConstraintBase):
    """解に必ず含めなければならない要素を列挙する制約(必須経由ノード等)。"""

    kind: Literal["required_inclusion"] = "required_inclusion"
    items: list[str]


class ForbiddenConstraint(ConstraintBase):
    """解に含めてはならない要素を列挙する制約(通行禁止エッジ等)。"""

    kind: Literal["forbidden"] = "forbidden"
    items: list[str]


class StaffingConstraint(ConstraintBase):
    """各スロットの必要人数を満たすことを要求する制約(詳細は data 側が持つ)。"""

    kind: Literal["staffing"] = "staffing"


class GenericConstraint(ConstraintBase):
    """専用サブタイプのない ad-hoc な制約。kind は任意の文字列。

    種類が固まったら専用サブタイプに昇格させる。ここは基底ではなく末端なので
    kind: str の宣言でも override 警告は出ない。
    """

    kind: str


# constraints の1要素の型(Phase-0-2.md §4.4)。
# union_mode="left_to_right": 左から順に検証を試し、既知サブタイプに当てはまらない kind は
# 末尾の GenericConstraint にフォールバックする。
# PEP 695 の `type` 文で型エイリアスを宣言する(Phase 0-2 の `: TypeAlias` から変更。
# ruff UP040 / pyright はこちらを推奨し、Annotated[..., Field(...)] も型として正しく扱う)。
type AnyConstraint = Annotated[
    NumericBoundConstraint
    | RequiredInclusionConstraint
    | ForbiddenConstraint
    | StaffingConstraint
    | GenericConstraint,
    Field(union_mode="left_to_right"),
]


# ---------------------------------------------------------------------------
# 問題固有データ(ProblemData): problem_type を判別子にした判別可能ユニオン
# ---------------------------------------------------------------------------

# discriminator="problem_type": 入力 dict の problem_type を見て正しいサブモデルを構築する。
# 新しい問題タイプは XxxData を定義してここに 1 項目足すだけ(既存に触れない)。
type ProblemData = Annotated[
    RouteData | ShiftData,
    Field(discriminator="problem_type"),
]


# ---------------------------------------------------------------------------
# 問題定義(OptimizationProblem)
# ---------------------------------------------------------------------------


class OptimizationProblem(BaseModel):
    """LLM(将来)と Algorithm Engine の共通言語。目的・制約・問題固有データを束ねる。"""

    problem_type: Literal["route_planning", "shift_scheduling"]
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
