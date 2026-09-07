// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BenchmarkResponse, SolveResponse } from "@/lib/api/types";
import { ROUTE_SAMPLES } from "../sample-problems";

const solveRoute = vi.fn();
const compareRoute = vi.fn();
vi.mock("../api/route-planner", () => ({
  solveRoute: (...a: unknown[]) => solveRoute(...a),
  compareRoute: (...a: unknown[]) => compareRoute(...a),
}));

import { useRoutePlannerStore } from "./route-planner-store";

const SOLVE: SolveResponse = {
  solution: {
    status: "valid",
    assignments: {
      problem_type: "route_planning",
      path_node_ids: ["A", "B", "D", "E"],
      path_edge_ids: ["e_ab", "e_bd", "e_de"],
      total_weight: 5,
    },
    metrics: { total_weight: 5, _ops: 5 },
    violations: [],
    produced_by: { name: "dijkstra", family: "graph", implementation: "handwritten" },
  },
  problem_id: null,
  solution_id: null,
};

const COMPARE: BenchmarkResponse = { entries: [], benchmark_id: null };

describe("route-planner-store", () => {
  beforeEach(() => {
    solveRoute.mockReset();
    compareRoute.mockReset();
    useRoutePlannerStore.getState().reset();
  });
  afterEach(() => vi.restoreAllMocks());

  it("solve stores the returned solution", async () => {
    solveRoute.mockResolvedValueOnce(SOLVE);
    await useRoutePlannerStore.getState().solve();
    expect(useRoutePlannerStore.getState().solveStatus).toBe("success");
    expect(useRoutePlannerStore.getState().solution?.assignments.total_weight).toBe(5);
  });

  it("solve records an error on failure", async () => {
    solveRoute.mockRejectedValueOnce(new Error("boom"));
    await useRoutePlannerStore.getState().solve();
    expect(useRoutePlannerStore.getState().solveStatus).toBe("error");
    expect(useRoutePlannerStore.getState().error).toBeTruthy();
  });

  it("compare stores the benchmark response", async () => {
    compareRoute.mockResolvedValueOnce(COMPARE);
    await useRoutePlannerStore.getState().compare();
    expect(useRoutePlannerStore.getState().compareStatus).toBe("success");
    expect(useRoutePlannerStore.getState().comparison).toEqual(COMPARE);
  });

  it("setProblem clears previous results", async () => {
    solveRoute.mockResolvedValueOnce(SOLVE);
    await useRoutePlannerStore.getState().solve();
    useRoutePlannerStore.getState().setProblem(ROUTE_SAMPLES[2].problem);
    expect(useRoutePlannerStore.getState().solution).toBeNull();
    expect(useRoutePlannerStore.getState().problem.data.problem_type).toBe("route_planning");
  });
});
