"""Phase 0-2 の共通スキーマのスケッチ。

decitima-api には未配線の「設計の例示」。Phase 1 で app/domain/ 配下へ
整理して実装する。ここでは Pydantic v2 で型の形だけを確認する。

実行例:
    uv run python -m py_compile textbook/Phase-0/samples/problem_schema.py
    （route_planner_example.py / shift_scheduler_example.py から import される）
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 目的（Objective）
# ---------------------------------------------------------------------------


class Objective(BaseModel):
    """最適化の目的を1つ表す。何を、どちら方向に良くしたいか。"""

    # sense: 最小化するか最大化するか
    sense: Literal["minimize", "maximize"]
    # target: 対象メトリクスの名前。計算方法はアルゴリズム側が解釈する
    target: str
    # weight: 多目的のときの相対的な重み。単一目的なら 1.0 のまま
    weight: float = 1.0
    description: str | None = None


# ---------------------------------------------------------------------------
# 制約（Constraint）
# ---------------------------------------------------------------------------


class Constraint(BaseModel):
    """守るべき条件を1つ表す基底クラス。kind ごとにサブタイプで具体化する。"""

    # kind: 制約の種類。判別子。サブタイプが Literal で固定する
    kind: str
    # severity: hard=絶対に破れない / soft=破れるがペナルティが付く
    severity: Literal["hard", "soft"] = "hard"
    # penalty: soft 制約を1件破るごとに目的関数へ加算するペナルティ
    penalty: float | None = None
    description: str | None = None


class NumericBoundConstraint(Constraint):
    """ある数値フィールドの上限・下限・等値を課す宣言的な制約。"""

    kind: Literal["numeric_bound"] = "numeric_bound"
    # field: 対象フィールド名（例: "weekly_work_hours"）
    field: str
    op: Literal["<=", ">=", "==", "<", ">"]
    value: float


class RequiredInclusionConstraint(Constraint):
    """解に必ず含めなければならない要素を列挙する制約（必須経由ノード等）。"""

    kind: Literal["required_inclusion"] = "required_inclusion"
    items: list[str]


class ForbiddenConstraint(Constraint):
    """解に含めてはならない要素を列挙する制約（通行禁止エッジ等）。"""

    kind: Literal["forbidden"] = "forbidden"
    items: list[str]


class StaffingConstraint(Constraint):
    """各スロットの必要人数を満たすことを要求する制約（詳細は data 側が持つ）。"""

    kind: Literal["staffing"] = "staffing"


# MVP で使う制約サブタイプの判別可能ユニオン。素の Constraint も許容する
AnyConstraint = Annotated[
    NumericBoundConstraint
    | RequiredInclusionConstraint
    | ForbiddenConstraint
    | StaffingConstraint
    | Constraint,
    Field(union_mode="left_to_right"),
]


# ---------------------------------------------------------------------------
# 問題固有データ（ProblemData）: problem_type を判別子にした union
# ---------------------------------------------------------------------------


class RouteNode(BaseModel):
    """経路問題のノード1つ。座標は A* のヒューリスティック用で任意。"""

    id: str
    label: str | None = None
    x: float | None = None
    y: float | None = None


class RouteEdge(BaseModel):
    """経路問題のエッジ1本。weight は距離または所要時間。"""

    id: str
    source: str
    target: str
    weight: float
    directed: bool = False


class RouteData(BaseModel):
    """Route Planner の問題固有データ。グラフと始点・終点。"""

    problem_type: Literal["route_planning"] = "route_planning"
    nodes: list[RouteNode]
    edges: list[RouteEdge]
    start: str
    goal: str


class Staff(BaseModel):
    """シフト問題のスタッフ1人。時給・スキル・勤務可能スロット・希望休。"""

    id: str
    name: str | None = None
    hourly_wage: float
    skills: list[str] = Field(default_factory=list)
    available_slot_ids: list[str] = Field(default_factory=list)
    requested_days_off: list[str] = Field(default_factory=list)


class ShiftSlot(BaseModel):
    """シフト問題の勤務スロット1つ。日付・時間帯・必要人数・必要スキル。"""

    id: str
    day: str
    start_hour: int
    end_hour: int
    required_headcount: int
    required_skills: list[str] = Field(default_factory=list)


class ShiftData(BaseModel):
    """Shift Scheduler の問題固有データ。スタッフ・スロット・全体上限。"""

    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    staff: list[Staff]
    slots: list[ShiftSlot]
    max_weekly_hours: float = 40
    max_consecutive_days: int = 5


ProblemData = Annotated[RouteData | ShiftData, Field(discriminator="problem_type")]


# ---------------------------------------------------------------------------
# 問題定義（OptimizationProblem）
# ---------------------------------------------------------------------------


class OptimizationProblem(BaseModel):
    """LLM と Algorithm Engine の共通言語。目的・制約・問題固有データを束ねる。"""

    problem_type: Literal["route_planning", "shift_scheduling"]
    objectives: list[Objective]
    constraints: list[AnyConstraint] = Field(default_factory=list)
    data: ProblemData
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# 解（CandidateSolution）
# ---------------------------------------------------------------------------


class ConstraintViolation(BaseModel):
    """検証で見つかった制約違反1件。どの制約を、どう破ったか。"""

    constraint_kind: str
    severity: Literal["hard", "soft"]
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class AlgorithmMeta(BaseModel):
    """解を生成したアルゴリズムの素性。比較可能性（NFR-3）の土台になる。"""

    name: str
    family: Literal["search", "graph", "optimization", "scheduling", "patterns"]
    # implementation: "handwritten" / "library:networkx" / "library:ortools" など
    implementation: str
    time_complexity: str | None = None
    space_complexity: str | None = None


class RouteSolution(BaseModel):
    """Route Planner の解。start から goal までのノード列とエッジ列。"""

    problem_type: Literal["route_planning"] = "route_planning"
    path_node_ids: list[str]
    path_edge_ids: list[str]
    total_weight: float


class ShiftSolution(BaseModel):
    """Shift Scheduler の解。スロット ID ごとに割り当てたスタッフ ID のリスト。"""

    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    assignments: dict[str, list[str]]


SolutionData = Annotated[RouteSolution | ShiftSolution, Field(discriminator="problem_type")]


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


if __name__ == "__main__":
    # スキーマが読み込めることの最小確認
    print("problem_schema OK:", OptimizationProblem.model_json_schema()["title"])
