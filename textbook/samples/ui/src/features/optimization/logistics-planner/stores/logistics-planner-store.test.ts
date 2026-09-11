// DeciTima samples │ Phase 9
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BenchmarkResponse, JobSubmitResponse, SolveResponse } from "@/lib/api/types";

const solveLogistics = vi.fn();
const compareLogistics = vi.fn();
vi.mock("../api/logistics-planner", () => ({
  solveLogistics: (...a: unknown[]) => solveLogistics(...a),
  compareLogistics: (...a: unknown[]) => compareLogistics(...a),
}));

const submitJob = vi.fn();
vi.mock("@/features/optimization/api/jobs", () => ({
  submitJob: (...a: unknown[]) => submitJob(...a),
}));

import { useLogisticsPlannerStore } from "./logistics-planner-store";

const SOLVE: SolveResponse = {
  solution: {
    status: "valid",
    assignments: {
      problem_type: "logistics_planning",
      routes: [
        { vehicle_id: "V1", stop_ids: ["P1", "P2"], distance: 9 },
        { vehicle_id: "V2", stop_ids: ["P3"], distance: 12 },
      ],
      total_distance: 21,
    },
    metrics: { total_distance: 21, vehicles_used: 2 },
    violations: [],
    produced_by: { name: "knapsack_dp", family: "optimization", implementation: "handwritten" },
  },
  problem_id: null,
  solution_id: null,
};

const COMPARE: BenchmarkResponse = { entries: [], benchmark_id: null };
const JOB_SUBMIT: JobSubmitResponse = { job_id: "job-1", status: "queued" };

describe("logistics-planner-store", () => {
  beforeEach(() => {
    solveLogistics.mockReset();
    compareLogistics.mockReset();
    submitJob.mockReset();
    useLogisticsPlannerStore.getState().reset();
  });
  afterEach(() => vi.restoreAllMocks());

  it("solve stores the routing plan", async () => {
    solveLogistics.mockResolvedValueOnce(SOLVE);
    await useLogisticsPlannerStore.getState().solve();
    expect(useLogisticsPlannerStore.getState().solveStatus).toBe("success");
    expect(useLogisticsPlannerStore.getState().solution?.metrics.total_distance).toBe(21);
  });

  it("compare stores the benchmark response", async () => {
    compareLogistics.mockResolvedValueOnce(COMPARE);
    await useLogisticsPlannerStore.getState().compare();
    expect(useLogisticsPlannerStore.getState().comparison).toEqual(COMPARE);
  });

  it("records an error on solve failure", async () => {
    solveLogistics.mockRejectedValueOnce(new Error("boom"));
    await useLogisticsPlannerStore.getState().solve();
    expect(useLogisticsPlannerStore.getState().solveStatus).toBe("error");
  });

  it("setProblem clears the previous solution and job id", async () => {
    solveLogistics.mockResolvedValueOnce(SOLVE);
    await useLogisticsPlannerStore.getState().solve();
    useLogisticsPlannerStore
      .getState()
      .setProblem(useLogisticsPlannerStore.getState().problem);
    expect(useLogisticsPlannerStore.getState().solution).toBeNull();
    expect(useLogisticsPlannerStore.getState().jobId).toBeNull();
  });

  it("submitAsJob stores the returned job id (does not fetch the result itself)", async () => {
    submitJob.mockResolvedValueOnce(JOB_SUBMIT);
    await useLogisticsPlannerStore.getState().submitAsJob("pulp_milp");
    expect(useLogisticsPlannerStore.getState().jobId).toBe("job-1");
    expect(useLogisticsPlannerStore.getState().jobStatus).toBe("success");
  });

  it("records an error when job submission fails", async () => {
    submitJob.mockRejectedValueOnce(new Error("boom"));
    await useLogisticsPlannerStore.getState().submitAsJob();
    expect(useLogisticsPlannerStore.getState().jobStatus).toBe("error");
    expect(useLogisticsPlannerStore.getState().jobId).toBeNull();
  });
});
