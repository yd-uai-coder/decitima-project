// DeciTima samples │ Phase 9
// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...a: unknown[]) => apiFetch(...a),
  ApiError: class ApiError extends Error {},
}));

import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";
import { getJobStatus, submitJob } from "./jobs";

describe("optimization/api/jobs", () => {
  afterEach(() => apiFetch.mockReset());

  it("submitJob POSTs the request body to /api/v1/jobs", async () => {
    apiFetch.mockResolvedValueOnce({ job_id: "j1", status: "queued" });
    await submitJob(SAMPLE_ROUTE_PROBLEM, "pulp_milp");
    const [path, init] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/v1/jobs");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body).algorithm).toBe("pulp_milp");
  });

  it("getJobStatus GETs /api/v1/jobs/{id}", async () => {
    apiFetch.mockResolvedValueOnce({ job_id: "j1", status: "succeeded" });
    await getJobStatus("j1");
    expect(apiFetch.mock.calls[0][0]).toBe("/api/v1/jobs/j1");
  });
});
