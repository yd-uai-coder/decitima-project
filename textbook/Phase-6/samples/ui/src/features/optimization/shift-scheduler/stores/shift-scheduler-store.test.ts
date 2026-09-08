// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BenchmarkResponse, SolveResponse } from "@/lib/api/types";

const solveShift = vi.fn();
const compareShift = vi.fn();
vi.mock("../api/shift-scheduler", () => ({
  solveShift: (...a: unknown[]) => solveShift(...a),
  compareShift: (...a: unknown[]) => compareShift(...a),
}));

import { useShiftSchedulerStore } from "./shift-scheduler-store";

const SOLVE: SolveResponse = {
  solution: {
    status: "valid",
    assignments: {
      problem_type: "shift_scheduling",
      assignments: { s1: ["sato"], s2: ["sato"], s3: ["sato"], s4: ["sato"] },
    },
    metrics: { labor_cost: 20000, day_off_satisfaction: 1, hour_variance: 88.9, _ops: 63 },
    violations: [],
    produced_by: { name: "backtracking", family: "scheduling", implementation: "handwritten" },
  },
  problem_id: null,
  solution_id: null,
};

const COMPARE: BenchmarkResponse = { entries: [], benchmark_id: null };

describe("shift-scheduler-store", () => {
  beforeEach(() => {
    solveShift.mockReset();
    compareShift.mockReset();
    useShiftSchedulerStore.getState().reset();
  });
  afterEach(() => vi.restoreAllMocks());

  it("solve stores the shift solution", async () => {
    solveShift.mockResolvedValueOnce(SOLVE);
    await useShiftSchedulerStore.getState().solve();
    expect(useShiftSchedulerStore.getState().solveStatus).toBe("success");
    expect(useShiftSchedulerStore.getState().solution?.metrics.labor_cost).toBe(20000);
  });

  it("solve forwards the requested algorithm", async () => {
    solveShift.mockResolvedValueOnce(SOLVE);
    await useShiftSchedulerStore.getState().solve("cp_sat");
    expect(solveShift).toHaveBeenCalledWith(expect.anything(), "cp_sat");
  });

  it("compare stores the benchmark response", async () => {
    compareShift.mockResolvedValueOnce(COMPARE);
    await useShiftSchedulerStore.getState().compare();
    expect(useShiftSchedulerStore.getState().comparison).toEqual(COMPARE);
  });

  it("records an error on failure", async () => {
    solveShift.mockRejectedValueOnce(new Error("boom"));
    await useShiftSchedulerStore.getState().solve();
    expect(useShiftSchedulerStore.getState().solveStatus).toBe("error");
  });
});
