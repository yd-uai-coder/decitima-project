// DeciTima samples │ 初出 Phase 14
// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...a: unknown[]) => apiFetch(...a),
  ApiError: class ApiError extends Error {},
}));

import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";
import { compareLlmVsAlgorithm } from "./compare";

describe("optimization/api/compare", () => {
  afterEach(() => apiFetch.mockReset());

  it("compareLlmVsAlgorithm POSTs { problem, llm_runs } to /api/v1/compare", async () => {
    apiFetch.mockResolvedValueOnce({
      problem_type: "route_planning",
      algorithm_used: { name: "dijkstra", family: "graph", implementation: "handwritten" },
      algorithm_result: {
        status: "valid",
        metrics: {},
        hard_violations: 0,
        soft_violations: 0,
        elapsed_ms: 1,
        error: null,
        structure_hash: "abc",
      },
      llm_results: [],
      metrics: {
        constraint_compliance_rate_algorithm: 1,
        constraint_compliance_rate_llm: 1,
        optimality_avg_quality_ratio_llm: 1,
        reproducibility_distinct_solutions_llm: 1,
        execution_time_ms_algorithm: 1,
        execution_time_ms_llm_median: 1,
        error_rate_llm: 0,
      },
      narrative: null,
      notes: [],
    });

    await compareLlmVsAlgorithm(SAMPLE_ROUTE_PROBLEM, 3);

    const [path, init] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/v1/compare");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.problem.problem_type).toBe("route_planning");
    expect(body.llm_runs).toBe(3);
  });
});
