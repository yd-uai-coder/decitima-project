// DeciTima samples │ 初出 Phase 13
// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...a: unknown[]) => apiFetch(...a),
  ApiError: class ApiError extends Error {},
}));

import { explainSolution } from "./explain";

describe("optimization/api/explain", () => {
  afterEach(() => apiFetch.mockReset());

  it("explainSolution POSTs to /api/v1/solutions/{id}/explain", async () => {
    apiFetch.mockResolvedValueOnce({
      solution_id: "s1",
      problem_type: "route_planning",
      algorithm_name: "dijkstra",
      why_this_solution: "x",
      key_constraints: "x",
      algorithm_rationale: "x",
      alternatives_comparison: "x",
      improvement_notes: "x",
      notes: [],
    });

    await explainSolution("s1");

    const [path, init] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/v1/solutions/s1/explain");
    expect(init.method).toBe("POST");
  });
});
