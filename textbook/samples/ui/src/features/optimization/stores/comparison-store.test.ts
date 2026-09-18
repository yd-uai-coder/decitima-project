// DeciTima samples │ 初出 Phase 14
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ComparisonResponse } from "@/lib/api/types";
import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";

const compareLlmVsAlgorithm = vi.fn();
vi.mock("../api/compare", () => ({
  compareLlmVsAlgorithm: (...a: unknown[]) => compareLlmVsAlgorithm(...a),
}));

import { useComparisonStore } from "./comparison-store";

const FAKE: ComparisonResponse = {
  problem_type: "route_planning",
  algorithm_used: { name: "dijkstra", family: "graph", implementation: "handwritten" },
  algorithm_result: {
    status: "valid",
    metrics: { total_weight: 5 },
    hard_violations: 0,
    soft_violations: 0,
    elapsed_ms: 1,
    error: null,
    structure_hash: "abc",
  },
  llm_results: [],
  metrics: {
    constraint_compliance_rate_algorithm: 1,
    constraint_compliance_rate_llm: 0.8,
    optimality_avg_quality_ratio_llm: 1.1,
    reproducibility_distinct_solutions_llm: 2,
    execution_time_ms_algorithm: 1,
    execution_time_ms_llm_median: 500,
    error_rate_llm: 0,
  },
  narrative: null,
  notes: [],
};

describe("comparison-store", () => {
  beforeEach(() => {
    compareLlmVsAlgorithm.mockReset();
    useComparisonStore.setState({ result: null, status: "idle", error: null, fetchedAt: null });
  });
  afterEach(() => vi.restoreAllMocks());

  it("stores the result on success", async () => {
    compareLlmVsAlgorithm.mockResolvedValueOnce(FAKE);
    await useComparisonStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(useComparisonStore.getState().status).toBe("success");
    expect(useComparisonStore.getState().result?.algorithm_used.name).toBe("dijkstra");
  });

  it("records an error message on failure", async () => {
    compareLlmVsAlgorithm.mockRejectedValueOnce(new Error("boom"));
    await useComparisonStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(useComparisonStore.getState().status).toBe("error");
    expect(useComparisonStore.getState().error).toBeTruthy();
  });

  it("skips a second run while the cache is fresh, unless forced", async () => {
    compareLlmVsAlgorithm.mockResolvedValue(FAKE);
    await useComparisonStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    await useComparisonStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(compareLlmVsAlgorithm).toHaveBeenCalledTimes(1);

    await useComparisonStore.getState().run(SAMPLE_ROUTE_PROBLEM, { force: true });
    expect(compareLlmVsAlgorithm).toHaveBeenCalledTimes(2);
  });

  it("passes llmRuns through to the API call", async () => {
    compareLlmVsAlgorithm.mockResolvedValueOnce(FAKE);
    await useComparisonStore.getState().run(SAMPLE_ROUTE_PROBLEM, { llmRuns: 10 });
    expect(compareLlmVsAlgorithm).toHaveBeenCalledWith(SAMPLE_ROUTE_PROBLEM, 10);
  });

  it("reset clears everything", async () => {
    compareLlmVsAlgorithm.mockResolvedValueOnce(FAKE);
    await useComparisonStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    useComparisonStore.getState().reset();
    expect(useComparisonStore.getState().result).toBeNull();
    expect(useComparisonStore.getState().status).toBe("idle");
  });
});
