// DeciTima samples │ Phase 7
import type { OptimizationProblem } from "@/lib/api/types";

const PLACES = [
  { id: "P0", name: "宿", value: 0, cost: 0, duration: 0 },
  { id: "P1", name: "美術館", value: 10, cost: 4, duration: 2 },
  { id: "P2", name: "公園", value: 8, cost: 3, duration: 3 },
  { id: "P3", name: "市場", value: 6, cost: 5, duration: 1 },
  { id: "P4", name: "展望台", value: 12, cost: 6, duration: 3 },
];

// 5 拠点のほぼ完全グラフ。移動は一律 cost 1 / time 1。
const LEGS = [
  ["P0", "P1"],
  ["P0", "P2"],
  ["P0", "P3"],
  ["P0", "P4"],
  ["P1", "P2"],
  ["P1", "P3"],
  ["P1", "P4"],
  ["P2", "P3"],
  ["P2", "P4"],
  ["P3", "P4"],
].map(([a, b]) => ({ id: `L_${a}${b}`, endpoints: [a, b] as [string, string], travel_cost: 1, travel_time: 1 }));

/** Travel Planner のデモ問題。backend の build_travel_problem と対応。 */
export const TRAVEL_SAMPLES: { label: string; problem: OptimizationProblem }[] = [
  {
    label: "予算ゆるめ(25 / 20)── DP も回れる",
    problem: {
      problem_type: "travel_planning",
      objectives: [{ sense: "maximize", target: "total_value" }],
      constraints: [],
      data: {
        problem_type: "travel_planning",
        places: PLACES,
        legs: LEGS,
        budget: 25,
        time_budget: 20,
        start: "P0",
        preferences: {},
      },
    },
  },
  {
    label: "予算きつめ(20 / 20)── DP は移動分で予算超過",
    problem: {
      problem_type: "travel_planning",
      objectives: [{ sense: "maximize", target: "total_value" }],
      constraints: [],
      data: {
        problem_type: "travel_planning",
        places: PLACES,
        legs: LEGS,
        budget: 20,
        time_budget: 20,
        start: "P0",
        preferences: {},
      },
    },
  },
  {
    label: "展望台を好み 1.5 倍・美術館は必須",
    problem: {
      problem_type: "travel_planning",
      objectives: [{ sense: "maximize", target: "total_value" }],
      constraints: [{ kind: "required_inclusion", severity: "hard", items: ["P1"] }],
      data: {
        problem_type: "travel_planning",
        places: PLACES,
        legs: LEGS,
        budget: 22,
        time_budget: 18,
        start: "P0",
        preferences: { P4: 1.5 },
      },
    },
  },
];
