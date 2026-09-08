// DeciTima samples │ Phase 5
import type { OptimizationProblem } from "@/lib/api/types";

/** Network Designer のデモ問題。backend の build_network_problem と対応(MST コスト 10)。 */
export const NETWORK_SAMPLES: { label: string; problem: OptimizationProblem }[] = [
  {
    label: "5 拠点(MST コスト 10)",
    problem: {
      problem_type: "network_design",
      objectives: [{ sense: "minimize", target: "total_weight" }],
      constraints: [],
      data: {
        problem_type: "network_design",
        nodes: [{ id: "A" }, { id: "B" }, { id: "C" }, { id: "D" }, { id: "E" }],
        links: [
          { id: "L_ab", endpoints: ["A", "B"], weight: 1 },
          { id: "L_bc", endpoints: ["B", "C"], weight: 2 },
          { id: "L_cd", endpoints: ["C", "D"], weight: 3 },
          { id: "L_be", endpoints: ["B", "E"], weight: 4 },
          { id: "L_ac", endpoints: ["A", "C"], weight: 5 },
          { id: "L_de", endpoints: ["D", "E"], weight: 6 },
          { id: "L_ae", endpoints: ["A", "E"], weight: 7 },
        ],
      },
    },
  },
  {
    label: "必須 L_ac・禁止 L_bc",
    problem: {
      problem_type: "network_design",
      objectives: [{ sense: "minimize", target: "total_weight" }],
      constraints: [
        { kind: "required_inclusion", severity: "hard", items: ["L_ac"] },
        { kind: "forbidden", severity: "hard", items: ["L_bc"] },
      ],
      data: {
        problem_type: "network_design",
        nodes: [{ id: "A" }, { id: "B" }, { id: "C" }, { id: "D" }, { id: "E" }],
        links: [
          { id: "L_ab", endpoints: ["A", "B"], weight: 1 },
          { id: "L_bc", endpoints: ["B", "C"], weight: 2 },
          { id: "L_cd", endpoints: ["C", "D"], weight: 3 },
          { id: "L_be", endpoints: ["B", "E"], weight: 4 },
          { id: "L_ac", endpoints: ["A", "C"], weight: 5 },
          { id: "L_de", endpoints: ["D", "E"], weight: 6 },
          { id: "L_ae", endpoints: ["A", "E"], weight: 7 },
        ],
      },
    },
  },
];
