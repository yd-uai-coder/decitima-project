// DeciTima samples │ 初出 Phase 12
// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...a: unknown[]) => apiFetch(...a),
  ApiError: class ApiError extends Error {},
}));

import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";
import { recommendAlgorithm } from "./recommend";

describe("optimization/api/recommend", () => {
  afterEach(() => apiFetch.mockReset());

  it("recommendAlgorithm POSTs { problem } to /api/v1/algorithms/recommend", async () => {
    apiFetch.mockResolvedValueOnce({
      problem_type: "route_planning",
      rule_preferred: "dijkstra",
      recommendations: [],
      notes: [],
    });

    await recommendAlgorithm(SAMPLE_ROUTE_PROBLEM);

    const [path, init] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/v1/algorithms/recommend");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body).problem.problem_type).toBe("route_planning");
  });
});
