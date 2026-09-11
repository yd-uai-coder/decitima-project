// DeciTima samples │ Phase 8
import type { OptimizationProblem } from "@/lib/api/types";

// backend の build_project_problem と対応する 5 タスクの例題。
const TASKS = [
  { id: "A", name: "設計", duration: 3, resource: 2 },
  { id: "B", name: "調達", duration: 2, resource: 1 },
  { id: "C", name: "実装", duration: 4, resource: 3 },
  { id: "D", name: "検証", duration: 2, resource: 1 },
  { id: "E", name: "リリース", duration: 1, resource: 2 },
];
const DEPS = [
  { id: "dep_ac", predecessor: "A", successor: "C" },
  { id: "dep_bd", predecessor: "B", successor: "D" },
  { id: "dep_ce", predecessor: "C", successor: "E" },
  { id: "dep_de", predecessor: "D", successor: "E" },
];

/** Project Manager のデモ問題。 */
export const PROJECT_SAMPLES: { label: string; problem: OptimizationProblem }[] = [
  {
    label: "資源上限 3 ── cpm は資源超過 / priority_list=10 / cp_sat=9",
    problem: {
      problem_type: "project_scheduling",
      objectives: [
        { sense: "minimize", target: "makespan" },
        { sense: "minimize", target: "peak_resource", weight: 0.1 },
      ],
      constraints: [],
      data: { problem_type: "project_scheduling", tasks: TASKS, dependencies: DEPS, resource_capacity: 3 },
    },
  },
  {
    label: "資源制約なし ── 純粋 CPM(makespan 8、クリティカルパス A→C→E)",
    problem: {
      problem_type: "project_scheduling",
      objectives: [{ sense: "minimize", target: "makespan" }],
      constraints: [],
      data: {
        problem_type: "project_scheduling",
        tasks: TASKS,
        dependencies: DEPS,
        resource_capacity: null,
      },
    },
  },
  {
    label: "納期 7 を課す ── numeric_bound で invalid になる",
    problem: {
      problem_type: "project_scheduling",
      objectives: [{ sense: "minimize", target: "makespan" }],
      constraints: [{ kind: "numeric_bound", severity: "hard", field: "makespan", operator: "<=", value: 7 }],
      data: {
        problem_type: "project_scheduling",
        tasks: TASKS,
        dependencies: DEPS,
        resource_capacity: null,
      },
    },
  },
];
