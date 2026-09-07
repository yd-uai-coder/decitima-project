import type { OptimizationProblem } from "@/lib/api/types";

/**
 * Route Planner のデモ問題。backend の tests/fixtures/optimization.py と対応。
 * 本格的な作図エディタは作らない ── 問題は JSON テキストエリアで編集する。
 */
export const ROUTE_SAMPLES: { label: string; problem: OptimizationProblem }[] = [
  {
    label: "基本(A→E、期待最短 5)",
    problem: {
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
    },
  },
  {
    label: "必須経由 B・C(順序最適化)",
    problem: {
      problem_type: "route_planning",
      objectives: [{ sense: "minimize", target: "total_weight" }],
      constraints: [{ kind: "required_inclusion", severity: "hard", items: ["B", "C"] }],
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
    },
  },
  {
    label: "負辺(S→A→B→T が直行より短い)",
    problem: {
      problem_type: "route_planning",
      objectives: [{ sense: "minimize", target: "total_weight" }],
      constraints: [],
      data: {
        problem_type: "route_planning",
        start: "S",
        goal: "T",
        allow_negative: true,
        nodes: [{ id: "S" }, { id: "A" }, { id: "B" }, { id: "T" }],
        edges: [
          { id: "s_t", source: "S", target: "T", weight: 5, directed: true },
          { id: "s_a", source: "S", target: "A", weight: 2, directed: true },
          { id: "a_b", source: "A", target: "B", weight: -4, directed: true },
          { id: "b_t", source: "B", target: "T", weight: 3, directed: true },
        ],
      },
    },
  },
];
