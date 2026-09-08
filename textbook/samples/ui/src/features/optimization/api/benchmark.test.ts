// DeciTima samples │ Phase 3
// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...a: unknown[]) => apiFetch(...a),
  ApiError: class ApiError extends Error {},
}));

import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";
import { getBenchmarkRun, runBenchmark } from "./benchmark";

describe("optimization/api/benchmark", () => {
  afterEach(() => apiFetch.mockReset());

  it("runBenchmark POSTs the request body to /api/v1/benchmark", async () => {
    apiFetch.mockResolvedValueOnce({ entries: [], benchmark_id: null });
    await runBenchmark({ problem: SAMPLE_ROUTE_PROBLEM, runs: 3 });
    const [path, init] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/v1/benchmark");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body).runs).toBe(3);
  });

  it("getBenchmarkRun GETs /api/v1/benchmarks/{id}", async () => {
    apiFetch.mockResolvedValueOnce({ id: "xyz", problem_type: "route_planning" });
    await getBenchmarkRun("xyz");
    expect(apiFetch.mock.calls[0][0]).toBe("/api/v1/benchmarks/xyz");
  });
});
