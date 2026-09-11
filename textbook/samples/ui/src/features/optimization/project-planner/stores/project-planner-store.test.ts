// DeciTima samples │ Phase 8
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BenchmarkResponse, SolveResponse } from "@/lib/api/types";

const solveProject = vi.fn();
const compareProject = vi.fn();
vi.mock("../api/project-planner", () => ({
  solveProject: (...a: unknown[]) => solveProject(...a),
  compareProject: (...a: unknown[]) => compareProject(...a),
}));

import { useProjectPlannerStore } from "./project-planner-store";

const SOLVE: SolveResponse = {
  solution: {
    status: "valid",
    assignments: {
      problem_type: "project_scheduling",
      task_order: ["B", "D", "A", "C", "E"],
      schedule: [
        { task_id: "A", start: 0, finish: 3, slack: 0 },
        { task_id: "B", start: 0, finish: 2, slack: 3 },
        { task_id: "C", start: 3, finish: 7, slack: 0 },
        { task_id: "D", start: 2, finish: 4, slack: 3 },
        { task_id: "E", start: 7, finish: 8, slack: 0 },
      ],
      critical_path: ["A", "C", "E"],
      makespan: 8,
    },
    metrics: { makespan: 8, peak_resource: 4 },
    violations: [],
    produced_by: { name: "cpm", family: "scheduling", implementation: "handwritten" },
  },
  problem_id: null,
  solution_id: null,
};

const COMPARE: BenchmarkResponse = { entries: [], benchmark_id: null };

describe("project-planner-store", () => {
  beforeEach(() => {
    solveProject.mockReset();
    compareProject.mockReset();
    useProjectPlannerStore.getState().reset();
  });
  afterEach(() => vi.restoreAllMocks());

  it("solve stores the schedule", async () => {
    solveProject.mockResolvedValueOnce(SOLVE);
    await useProjectPlannerStore.getState().solve();
    expect(useProjectPlannerStore.getState().solveStatus).toBe("success");
    expect(useProjectPlannerStore.getState().solution?.metrics.makespan).toBe(8);
  });

  it("compare stores the benchmark response", async () => {
    compareProject.mockResolvedValueOnce(COMPARE);
    await useProjectPlannerStore.getState().compare();
    expect(useProjectPlannerStore.getState().comparison).toEqual(COMPARE);
  });

  it("records an error on failure", async () => {
    solveProject.mockRejectedValueOnce(new Error("boom"));
    await useProjectPlannerStore.getState().solve();
    expect(useProjectPlannerStore.getState().solveStatus).toBe("error");
  });

  it("setProblem clears the previous solution", async () => {
    solveProject.mockResolvedValueOnce(SOLVE);
    await useProjectPlannerStore.getState().solve();
    useProjectPlannerStore.getState().setProblem(useProjectPlannerStore.getState().problem);
    expect(useProjectPlannerStore.getState().solution).toBeNull();
  });
});
