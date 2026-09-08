// DeciTima samples │ Phase 3
import type { OptimizationProblem } from "@/lib/api/types";

/**
 * ベンチマーク画面のデモ用の route_planning 問題。backend の
 * tests/fixtures/optimization.py::build_route_problem と同じ例題(A→E、期待最短 5)。
 * 本番の問題定義入力 UI は Phase 4(Route Planner)。
 */
export const SAMPLE_ROUTE_PROBLEM: OptimizationProblem = {
  problem_type: "route_planning",
  objectives: [{ sense: "minimize", target: "total_weight" }],
  constraints: [],
  data: {
    problem_type: "route_planning",
    start: "A",
    goal: "E",
    nodes: [{ id: "A" }, { id: "B" }, { id: "C" }, { id: "D" }, { id: "E" }],
    edges: [
      { id: "e_ab", source: "A", target: "B", weight: 2 },
      { id: "e_bc", source: "B", target: "C", weight: 3 },
      { id: "e_bd", source: "B", target: "D", weight: 1 },
      { id: "e_ce", source: "C", target: "E", weight: 4 },
      { id: "e_de", source: "D", target: "E", weight: 2 },
    ],
  },
};
