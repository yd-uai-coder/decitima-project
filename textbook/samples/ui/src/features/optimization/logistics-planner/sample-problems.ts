// DeciTima samples │ Phase 9
import type { OptimizationProblem } from "@/lib/api/types";

// backend の build_logistics_problem(tests/fixtures/optimization.py)と対応する最小例。
// 容量 10 に対し demand は P1=4, P2=5, P3=7 ── P1+P2=9 は収まるが P1+P3=11 / P2+P3=12 は
// 超えるので、2 台に分けるなら {P1,P2} + {P3} の一択(総距離 21、使用台数 2)。
const NODES = [
  { id: "D", label: "デポ" },
  { id: "N1", label: "配送先1" },
  { id: "N2", label: "配送先2" },
  { id: "N3", label: "配送先3" },
];
const SEGMENTS = [
  { id: "S_D1", source: "D", target: "N1", distance: 4 },
  { id: "S_D2", source: "D", target: "N2", distance: 3 },
  { id: "S_D3", source: "D", target: "N3", distance: 6 },
  { id: "S_12", source: "N1", target: "N2", distance: 2 },
  { id: "S_23", source: "N2", target: "N3", distance: 3 },
];

// 少し規模を大きくした例(配送先6件・車両3台)。knapsack_dp / greedy / branch_and_bound /
// brute_force / pulp_milp を「比較」ボタンで並べ、総距離・使用台数の違いを確認できる。
const NODES_6 = [
  { id: "D", label: "デポ" },
  { id: "N1", label: "配送先1" },
  { id: "N2", label: "配送先2" },
  { id: "N3", label: "配送先3" },
  { id: "N4", label: "配送先4" },
  { id: "N5", label: "配送先5" },
  { id: "N6", label: "配送先6" },
];
const SEGMENTS_6 = [
  { id: "S_D1", source: "D", target: "N1", distance: 3 },
  { id: "S_D2", source: "D", target: "N2", distance: 4 },
  { id: "S_12", source: "N1", target: "N2", distance: 2 },
  { id: "S_23", source: "N2", target: "N3", distance: 3 },
  { id: "S_34", source: "N3", target: "N4", distance: 2 },
  { id: "S_15", source: "N1", target: "N5", distance: 5 },
  { id: "S_56", source: "N5", target: "N6", distance: 3 },
  { id: "S_46", source: "N4", target: "N6", distance: 4 },
];

/** Logistics Optimizer のデモ問題。 */
export const LOGISTICS_SAMPLES: { label: string; problem: OptimizationProblem }[] = [
  {
    label: "容量ぎりぎり ── 2台に分けるしかない(総距離21が唯一の実行可能解)",
    problem: {
      problem_type: "logistics_planning",
      objectives: [{ sense: "minimize", target: "total_distance" }],
      constraints: [],
      data: {
        problem_type: "logistics_planning",
        depot_id: "D",
        nodes: NODES,
        segments: SEGMENTS,
        vehicles: [
          { id: "V1", capacity_weight: 10, capacity_volume: 10 },
          { id: "V2", capacity_weight: 10, capacity_volume: 10 },
        ],
        deliveries: [
          { id: "P1", node_id: "N1", demand_weight: 4, demand_volume: 4 },
          { id: "P2", node_id: "N2", demand_weight: 5, demand_volume: 5 },
          { id: "P3", node_id: "N3", demand_weight: 7, demand_volume: 7 },
        ],
      },
    },
  },
  {
    label: "配送先6件・車両3台 ── strategy による総距離・使用台数の差を比較してみる",
    problem: {
      problem_type: "logistics_planning",
      objectives: [{ sense: "minimize", target: "total_distance" }],
      constraints: [],
      data: {
        problem_type: "logistics_planning",
        depot_id: "D",
        nodes: NODES_6,
        segments: SEGMENTS_6,
        vehicles: [
          { id: "V1", capacity_weight: 10, capacity_volume: 10 },
          { id: "V2", capacity_weight: 10, capacity_volume: 10 },
          { id: "V3", capacity_weight: 10, capacity_volume: 10 },
        ],
        deliveries: [
          { id: "P1", node_id: "N1", demand_weight: 3, demand_volume: 3 },
          { id: "P2", node_id: "N2", demand_weight: 4, demand_volume: 3 },
          { id: "P3", node_id: "N3", demand_weight: 2, demand_volume: 2 },
          { id: "P4", node_id: "N4", demand_weight: 3, demand_volume: 4 },
          { id: "P5", node_id: "N5", demand_weight: 2, demand_volume: 2 },
          { id: "P6", node_id: "N6", demand_weight: 3, demand_volume: 3 },
        ],
      },
    },
  },
];
