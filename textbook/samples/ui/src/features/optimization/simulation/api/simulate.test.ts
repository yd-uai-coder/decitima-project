// DeciTima samples │ Phase 10
// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...a: unknown[]) => apiFetch(...a),
  ApiError: class ApiError extends Error {},
}));

import { SAMPLE_ROUTE_PROBLEM } from "../../sample-problems";
import { submitSimulation } from "./simulate";

describe("optimization/simulation/api/simulate", () => {
  afterEach(() => apiFetch.mockReset());

  it("submitSimulation POSTs the request body to /api/v1/simulate", async () => {
    apiFetch.mockResolvedValueOnce({ job_id: "j1", status: "queued" });
    await submitSimulation({
      problem: SAMPLE_ROUTE_PROBLEM,
      scenarios: [{ label: "as-is", overrides: {} }],
    });
    const [path, init] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/v1/simulate");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body).scenarios).toEqual([{ label: "as-is", overrides: {} }]);
  });
});
