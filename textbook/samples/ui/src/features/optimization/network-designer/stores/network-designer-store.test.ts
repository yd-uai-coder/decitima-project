// DeciTima samples │ 初出 Phase 5 │ 改訂 Phase 6
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BenchmarkResponse, SolveResponse } from "@/lib/api/types";

const solveNetwork = vi.fn();
const compareNetwork = vi.fn();
vi.mock("../api/network-designer", () => ({
  solveNetwork: (...a: unknown[]) => solveNetwork(...a),
  compareNetwork: (...a: unknown[]) => compareNetwork(...a),
}));

import { useNetworkDesignerStore } from "./network-designer-store";

const SOLVE: SolveResponse = {
  solution: {
    status: "valid",
    assignments: {
      problem_type: "network_design",
      selected_link_ids: ["L_ab", "L_bc", "L_cd", "L_be"],
      total_weight: 10,
    },
    metrics: { total_weight: 10, _ops: 4 },
    violations: [],
    produced_by: { name: "kruskal", family: "graph", implementation: "handwritten" },
  },
  problem_id: null,
  solution_id: null,
};

const COMPARE: BenchmarkResponse = { entries: [], benchmark_id: null };

describe("network-designer-store", () => {
  beforeEach(() => {
    solveNetwork.mockReset();
    compareNetwork.mockReset();
    useNetworkDesignerStore.getState().reset();
  });
  afterEach(() => vi.restoreAllMocks());

  it("solve stores the MST solution", async () => {
    solveNetwork.mockResolvedValueOnce(SOLVE);
    await useNetworkDesignerStore.getState().solve();
    expect(useNetworkDesignerStore.getState().solveStatus).toBe("success");
    expect(useNetworkDesignerStore.getState().solution?.metrics.total_weight).toBe(10);
  });

  it("compare stores the benchmark response", async () => {
    compareNetwork.mockResolvedValueOnce(COMPARE);
    await useNetworkDesignerStore.getState().compare();
    expect(useNetworkDesignerStore.getState().comparison).toEqual(COMPARE);
  });

  it("records an error on failure", async () => {
    solveNetwork.mockRejectedValueOnce(new Error("boom"));
    await useNetworkDesignerStore.getState().solve();
    expect(useNetworkDesignerStore.getState().solveStatus).toBe("error");
  });
});
