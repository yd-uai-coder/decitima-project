// DeciTima samples │ 初出 Phase 13
// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...a: unknown[]) => apiFetch(...a),
  ApiError: class ApiError extends Error {},
}));

import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";
import { persistSolve } from "./solve";

describe("optimization/api/solve", () => {
  afterEach(() => apiFetch.mockReset());

  it("persistSolve POSTs { problem, persist: true } to /api/v1/solve", async () => {
    apiFetch.mockResolvedValueOnce({
      solution: { status: "valid", assignments: {}, metrics: {}, violations: [], produced_by: {} },
      problem_id: "p1",
      solution_id: "s1",
    });

    await persistSolve(SAMPLE_ROUTE_PROBLEM);

    const [path, init] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/v1/solve");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.persist).toBe(true);
    expect(body.problem.problem_type).toBe("route_planning");
  });

  it("passes the requested algorithm through", async () => {
    apiFetch.mockResolvedValueOnce({
      solution: { status: "valid", assignments: {}, metrics: {}, violations: [], produced_by: {} },
      problem_id: "p1",
      solution_id: "s1",
    });

    await persistSolve(SAMPLE_ROUTE_PROBLEM, "bellman_ford");

    const body = JSON.parse(apiFetch.mock.calls[0][1].body);
    expect(body.algorithm).toBe("bellman_ford");
  });
});
