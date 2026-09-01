"""SolutionVerificationService ── 解の制約充足(候補解が出た後)。

設計は Phase-0-6.md §3。Phase 1 は **route_planning 限定の最小実装**。
- 構造チェック(経路が連結 / start で始まり goal で終わる / total_weight 整合)は
  route 解に常に走らせる。
- kind ごとの Checker ディスパッチの「枠」(_CHECKERS)は用意し、Phase 1 では
  forbidden / required_inclusion の 2 つだけ実装する。
- hard 違反が1つでもあれば status="invalid"。soft 違反は soft_penalty を metrics に加算。
- 解は書き換えず model_copy(update=...) で新インスタンスを返す(生の解を監査用に残す)。
- kind ごとの Checker 全実装 / shift の Verification / invalid 解ハンドリングは Phase 2。
"""

# [以降 Phase で修正予定 ── Phase 2-3 / 2-4] このファイルの Phase 1 版はこのまま(スナップショット)。
# Phase 2-3 / 2-4 で:
#   - 構造検証を app/domain/solutions/structure.py(route + shift)へ移設
#   - kind ごとのチェッカーを app/domain/constraints/(CHECKERS レジストリ)へ移設
#   - このサービスは「構造検証 → metrics enrich → kind ディスパッチ → 集計」の純粋な
#     オーケストレーションに縮小
# 解決される問題: shift 解の未検証、numeric_bound/staffing の未対応、制約 kind 追加時のサービス改修。
# 現行版 textbook/Phase-2/samples/app/services/verification.py。詳細 Phase-2-3.md / Phase-2-4.md。

from __future__ import annotations

from collections.abc import Callable

from app.domain.problems.problem import (
    ForbiddenConstraint,
    OptimizationProblem,
    RequiredInclusionConstraint,
)
from app.domain.problems.route_planner import RouteData
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import CandidateSolution, ConstraintViolation

# kind -> チェッカー関数(constraint, problem, solution) -> ConstraintViolation | None
_Checker = Callable[..., "ConstraintViolation | None"]


class SolutionVerificationService:
    """候補解が problem のすべての制約を満たすか検証し、status と violations を確定する。"""

    def verify(
        self, problem: OptimizationProblem, solution: CandidateSolution
    ) -> CandidateSolution:
        if solution.status == "infeasible":
            return solution  # 解が無いものは検証しない

        violations: list[ConstraintViolation] = []

        # route 解の構造チェック(制約 kind に紐づかない、常に必要な検査)
        if isinstance(solution.assignments, RouteSolution) and isinstance(problem.data, RouteData):
            violations.extend(_verify_route_structure(problem.data, solution.assignments))

        # 制約 kind ごとにディスパッチ
        for c in problem.constraints:
            checker = _CHECKERS.get(c.kind)
            if checker is None:
                continue  # 未対応 kind は素通し(Phase 2 で埋める)
            v = checker(c, problem, solution)
            if v is not None:
                violations.append(v)

        has_hard = any(v.severity == "hard" for v in violations)
        soft_penalty = _soft_penalty(problem, violations)

        return solution.model_copy(
            update={
                "status": "invalid" if has_hard else solution.status,
                "violations": violations,
                "metrics": {**solution.metrics, "soft_penalty": soft_penalty},
            }
        )


# ---------------------------------------------------------------------------
# route の検査関数
# ---------------------------------------------------------------------------


def _verify_route_structure(data: RouteData, sol: RouteSolution) -> list[ConstraintViolation]:
    """経路が連結・始終点・weight 整合を満たすか。すべて hard。"""
    out: list[ConstraintViolation] = []
    edge_by_id = {e.id: e for e in data.edges}

    # 始点・終点
    if not sol.path_node_ids or sol.path_node_ids[0] != data.start:
        out.append(_hard("route_structure", f"path does not start at {data.start!r}"))
    if not sol.path_node_ids or sol.path_node_ids[-1] != data.goal:
        out.append(_hard("route_structure", f"path does not end at {data.goal!r}"))

    # ノード列とエッジ列の長さ整合
    if len(sol.path_edge_ids) != max(len(sol.path_node_ids) - 1, 0):
        out.append(_hard("route_structure", "path_edge_ids length != path_node_ids length - 1"))
        return out  # 以降の照合は成り立たないので打ち切り

    # 各エッジが隣接ノード対を実際に結んでいるか + weight 合計
    total = 0.0
    for i, edge_id in enumerate(sol.path_edge_ids):
        edge = edge_by_id.get(edge_id)
        a, b = sol.path_node_ids[i], sol.path_node_ids[i + 1]
        if edge is None:
            out.append(_hard("route_structure", f"unknown edge {edge_id!r} in path"))
            continue
        endpoints = {edge.source, edge.target}
        if endpoints != {a, b} and not (edge.directed and (edge.source, edge.target) == (a, b)):
            out.append(_hard("route_structure", f"edge {edge_id!r} does not connect {a!r}-{b!r}"))
        total += edge.weight

    if abs(total - sol.total_weight) > 1e-9:
        out.append(
            _hard(
                "route_structure",
                f"total_weight {sol.total_weight} != edge sum {total}",
            )
        )
    return out


def _check_forbidden(
    constraint: ForbiddenConstraint,
    problem: OptimizationProblem,
    solution: CandidateSolution,
) -> ConstraintViolation | None:
    """解が ForbiddenConstraint の要素(禁止エッジ id)を含んでいないか。"""
    assert isinstance(solution.assignments, RouteSolution)
    used = set(solution.assignments.path_edge_ids)
    hit = used & set(constraint.items)
    if not hit:
        return None
    return ConstraintViolation(
        constraint_kind=constraint.kind,
        severity=constraint.severity,
        message=f"path uses forbidden edge(s): {sorted(hit)}",
        detail={"forbidden_hit": sorted(hit)},
    )


def _check_required_inclusion(
    constraint: RequiredInclusionConstraint,
    problem: OptimizationProblem,
    solution: CandidateSolution,
) -> ConstraintViolation | None:
    """解が RequiredInclusionConstraint の要素(必須経由ノード id)をすべて通っているか。"""
    assert isinstance(solution.assignments, RouteSolution)
    visited = set(solution.assignments.path_node_ids)
    missing = set(constraint.items) - visited
    if not missing:
        return None
    return ConstraintViolation(
        constraint_kind=constraint.kind,
        severity=constraint.severity,
        message=f"path misses required node(s): {sorted(missing)}",
        detail={"missing": sorted(missing)},
    )


_CHECKERS: dict[str, _Checker] = {
    "forbidden": _check_forbidden,
    "required_inclusion": _check_required_inclusion,
    # "numeric_bound" / "staffing" などは Phase 2
}


def _hard(kind: str, message: str) -> ConstraintViolation:
    return ConstraintViolation(constraint_kind=kind, severity="hard", message=message)


def _soft_penalty(problem: OptimizationProblem, violations: list[ConstraintViolation]) -> float:
    """違反した soft 制約の penalty 合計。Phase 1 は kind 一致で素朴に対応付ける
    (同一 kind の soft 制約が複数あるケースの厳密な対応は Phase 2)。"""
    violated_kinds = {v.constraint_kind for v in violations if v.severity == "soft"}
    return sum(
        (c.penalty or 0.0)
        for c in problem.constraints
        if c.severity == "soft" and c.kind in violated_kinds
    )
