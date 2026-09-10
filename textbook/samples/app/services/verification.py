# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 2,5,7
"""SolutionVerificationService ── 解の制約充足(候補解が出た後)。

- 解の型ごとの「構造検証」は app/domain/solutions/structure.py(純粋述語)。
- 制約 kind ごとのチェッカーは app/domain/constraints/(CHECKERS レジストリ)。
- グラフ計算が要る検査だけはここで呼ぶ(domain は algorithms を import しない):
  network_design の「選んだリンクが全域木か」= `connectivity.forms_spanning_tree`(Phase 5-3)、
  travel_planning の「申告した total_cost / total_time が実際の巡回コストと合うか」=
  `travel_common.tour_cost`(Phase 7-4。Floyd-Warshall の再計算 ── `travel_common` が生まれる 7-4)。
  route の到達可能性を validation.py に置くのと同じ切り分け(`Phase-2-2.md` §3)。
"""

from __future__ import annotations

from app.algorithms.graph.connectivity import forms_spanning_tree
from app.algorithms.optimization.travel_common import all_pairs, tour_cost  # (Phase 7-4)
from app.domain.constraints import CHECKERS
from app.domain.problems.network_design import NetworkDesignData
from app.domain.problems.problem import OptimizationProblem
from app.domain.problems.travel_planner import TravelData  # (Phase 7-4)
from app.domain.solutions.network_design import NetworkDesignSolution
from app.domain.solutions.solution import CandidateSolution, ConstraintViolation
from app.domain.solutions.structure import structural_verify
from app.domain.solutions.travel_planner import TravelSolution  # (Phase 7-4)


class SolutionVerificationService:
    """候補解が problem のすべての制約を満たすか検証し、status と violations を確定する。"""

    def verify(
        self, problem: OptimizationProblem, solution: CandidateSolution
    ) -> CandidateSolution:
        if solution.status == "infeasible":
            return solution  # 解が無いものは検証しない

        # 1. 構造検証(純粋述語)+ グラフ計算が要る検査 + 追加メトリクス
        structural, extra_metrics = structural_verify(problem, solution)
        structural = [
            *structural,
            *_verify_spanning_tree(problem, solution),
            *_verify_travel_plan(problem, solution),  # (Phase 7-4)
        ]
        enriched = solution.model_copy(update={"metrics": {**solution.metrics, **extra_metrics}})

        # 2. 制約 kind ごとのチェッカー。enriched の metrics(構造検証後)を読む
        kind_violations: list[ConstraintViolation] = []
        for c in problem.constraints:
            checker = CHECKERS.get(c.kind)
            if checker is None:
                continue  # 未対応 kind は素通し
            v = checker(c, problem, enriched)
            if v is not None:
                kind_violations.append(v)

        violations = [*structural, *kind_violations]
        has_hard = any(v.severity == "hard" for v in violations)

        return enriched.model_copy(
            update={
                "status": "invalid" if has_hard else enriched.status,
                "violations": violations,
                "metrics": {
                    **enriched.metrics,
                    "soft_penalty": _soft_penalty(problem, violations),
                },
            }
        )


def _verify_spanning_tree(
    problem: OptimizationProblem, solution: CandidateSolution
) -> list[ConstraintViolation]:
    """network_design 解: 選んだリンクが全拠点を繋ぐ木になっているか。"""
    if not (
        isinstance(problem.data, NetworkDesignData)
        and isinstance(solution.assignments, NetworkDesignSolution)
    ):
        return []
    link_by_id = {link.id: link for link in problem.data.links}
    pairs = [
        link_by_id[lid].endpoints
        for lid in solution.assignments.selected_link_ids
        if lid in link_by_id
    ]
    node_ids = [n.id for n in problem.data.nodes]
    if forms_spanning_tree(node_ids, pairs):
        return []
    return [
        ConstraintViolation(
            constraint_kind="network_structure",
            severity="hard",
            message="selected links do not form a spanning tree (connect all nodes, no cycle)",
        )
    ]


# (Phase 7-4) travel_common(all_pairs / tour_cost)が揃う 7-4 で追加。7-3 では書かない。
def _verify_travel_plan(
    problem: OptimizationProblem, solution: CandidateSolution
) -> list[ConstraintViolation]:
    """travel_planning 解: 申告した total_cost / total_time が実際の巡回コストと合うか。

    Floyd-Warshall で全点対距離を出し直し、solution.visit_order の順(再最適化しない)で
    place + 移動のコストを積んで比べる。合わなければ strategy が嘘をついている(hard)。
    """
    if not (
        isinstance(problem.data, TravelData) and isinstance(solution.assignments, TravelSolution)
    ):
        return []
    cost_dist, time_dist = all_pairs(problem.data)
    real_cost, real_time = tour_cost(
        problem.data, solution.assignments.visit_order, cost_dist, time_dist
    )
    out: list[ConstraintViolation] = []
    if abs(real_cost - solution.assignments.total_cost) > 1e-6:
        out.append(
            ConstraintViolation(
                constraint_kind="travel_structure",
                severity="hard",
                message=f"claimed total_cost {solution.assignments.total_cost} "
                f"!= recomputed {real_cost}",
            )
        )
    if abs(real_time - solution.assignments.total_time) > 1e-6:
        out.append(
            ConstraintViolation(
                constraint_kind="travel_structure",
                severity="hard",
                message=f"claimed total_time {solution.assignments.total_time} "
                f"!= recomputed {real_time}",
            )
        )
    return out


def _soft_penalty(problem: OptimizationProblem, violations: list[ConstraintViolation]) -> float:
    """違反した soft 制約の penalty 合計。kind 一致で素朴に対応付ける。"""
    violated_kinds = {v.constraint_kind for v in violations if v.severity == "soft"}
    return sum(
        (c.penalty or 0.0)
        for c in problem.constraints
        if c.severity == "soft" and c.kind in violated_kinds
    )
