// DeciTima samples │ Phase 7
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BenchmarkResponse, SolveResponse } from "@/lib/api/types";

const solveTravel = vi.fn();
const compareTravel = vi.fn();
vi.mock("../api/travel-planner", () => ({
  solveTravel: (...a: unknown[]) => solveTravel(...a),
  compareTravel: (...a: unknown[]) => compareTravel(...a),
}));

import { useTravelPlannerStore } from "./travel-planner-store";

const SOLVE: SolveResponse = {
  solution: {
    status: "valid",
    assignments: {
      problem_type: "travel_planning",
      selected_place_ids: ["P0", "P1", "P4"],
      visit_order: ["P0", "P1", "P4"],
      total_value: 22,
      total_cost: 13,
      total_time: 8,
    },
    metrics: { total_value: 22, total_cost: 13, total_time: 8, _ops: 7 },
    violations: [],
    produced_by: { name: "knapsack_dp", family: "optimization", implementation: "handwritten" },
  },
  problem_id: null,
  solution_id: null,
};

const COMPARE: BenchmarkResponse = { entries: [], benchmark_id: null };

describe("travel-planner-store", () => {
  beforeEach(() => {
    solveTravel.mockReset();
    compareTravel.mockReset();
    useTravelPlannerStore.getState().reset();
  });
  afterEach(() => vi.restoreAllMocks());

  it("solve stores the travel plan", async () => {
    solveTravel.mockResolvedValueOnce(SOLVE);
    await useTravelPlannerStore.getState().solve();
    expect(useTravelPlannerStore.getState().solveStatus).toBe("success");
    expect(useTravelPlannerStore.getState().solution?.metrics.total_value).toBe(22);
  });

  it("compare stores the benchmark response", async () => {
    compareTravel.mockResolvedValueOnce(COMPARE);
    await useTravelPlannerStore.getState().compare();
    expect(useTravelPlannerStore.getState().comparison).toEqual(COMPARE);
  });

  it("records an error on failure", async () => {
    solveTravel.mockRejectedValueOnce(new Error("boom"));
    await useTravelPlannerStore.getState().solve();
    expect(useTravelPlannerStore.getState().solveStatus).toBe("error");
  });

  it("setProblem clears the previous solution", async () => {
    solveTravel.mockResolvedValueOnce(SOLVE);
    await useTravelPlannerStore.getState().solve();
    useTravelPlannerStore.getState().setProblem(useTravelPlannerStore.getState().problem);
    expect(useTravelPlannerStore.getState().solution).toBeNull();
  });
});
