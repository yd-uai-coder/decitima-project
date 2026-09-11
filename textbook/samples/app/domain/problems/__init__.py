# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 5,7,8
"""問題定義パッケージ。分割したファイルの内訳を利用側に見せない「公開窓口」。

利用側は `from app.domain.problems import OptimizationProblem, RouteData` と書け、
あとでファイルを分割・統合しても import 文が変わらない。

ユニオン(ProblemData)を __init__.py に置くと problem.py <-> __init__.py が循環するので、
ユニオンの定義は problem.py に置き、ここは re-export だけにする(ruff F401 対策で __all__)。

Phase 5-3 で network_design を、Phase 7-3 で travel_planning(Place / TravelLeg / TravelData)を、
Phase 8-3 で project_scheduling(ProjectTask / TaskDependency / ProjectData)を追加。
"""

from app.domain.problems.network_design import (
    NetworkDesignData,
    NetworkLink,
    NetworkNode,
)
from app.domain.problems.problem import (
    AnyConstraint,
    ConstraintBase,
    ForbiddenConstraint,
    GenericConstraint,
    NumericBoundConstraint,
    Objective,
    OptimizationProblem,
    ProblemData,
    RequiredInclusionConstraint,
    StaffingConstraint,
)
from app.domain.problems.project_manager import (  # (Phase 8-3)
    ProjectData,
    ProjectTask,
    TaskDependency,
)
from app.domain.problems.route_planner import RouteData, RouteEdge, RouteNode
from app.domain.problems.shift_scheduler import ShiftData, ShiftSlot, Staff
from app.domain.problems.travel_planner import Place, TravelData, TravelLeg  # (Phase 7-3)

__all__ = [
    "AnyConstraint",
    "ConstraintBase",
    "ForbiddenConstraint",
    "GenericConstraint",
    "NetworkDesignData",
    "NetworkLink",
    "NetworkNode",
    "NumericBoundConstraint",
    "Objective",
    "OptimizationProblem",
    "Place",
    "ProblemData",
    "ProjectData",
    "ProjectTask",
    "RequiredInclusionConstraint",
    "RouteData",
    "RouteEdge",
    "RouteNode",
    "ShiftData",
    "ShiftSlot",
    "Staff",
    "StaffingConstraint",
    "TaskDependency",
    "TravelData",
    "TravelLeg",
]
