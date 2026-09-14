// DeciTima samples │ Phase 10
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const submitSimulation = vi.fn();
vi.mock("../api/simulate", () => ({
  submitSimulation: (...a: unknown[]) => submitSimulation(...a),
}));

import { useSimulationStore } from "./simulation-store";

describe("simulation-store", () => {
  beforeEach(() => {
    submitSimulation.mockReset();
    useSimulationStore.getState().reset();
  });
  afterEach(() => vi.restoreAllMocks());

  it("submit stores the returned job_id", async () => {
    submitSimulation.mockResolvedValueOnce({ job_id: "job-1", status: "queued" });
    await useSimulationStore.getState().submit();
    expect(useSimulationStore.getState().jobId).toBe("job-1");
    expect(useSimulationStore.getState().submitStatus).toBe("success");
  });

  it("setScenarios clears a stale jobId so polling stops watching the old job", async () => {
    submitSimulation.mockResolvedValueOnce({ job_id: "job-1", status: "queued" });
    await useSimulationStore.getState().submit();
    useSimulationStore.getState().setScenarios([{ label: "tighter", overrides: {} }]);
    expect(useSimulationStore.getState().jobId).toBeNull();
  });

  it("records an error on failure", async () => {
    submitSimulation.mockRejectedValueOnce(new Error("boom"));
    await useSimulationStore.getState().submit();
    expect(useSimulationStore.getState().submitStatus).toBe("error");
    expect(useSimulationStore.getState().jobId).toBeNull();
  });
});
