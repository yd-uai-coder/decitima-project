// DeciTima samples │ Phase 3
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BenchmarkResponse } from "@/lib/api/types";
import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";

const runBenchmark = vi.fn();
vi.mock("../api/benchmark", () => ({ runBenchmark: (...a: unknown[]) => runBenchmark(...a) }));

import { useBenchmarkStore } from "./benchmark-store";

const FAKE: BenchmarkResponse = {
  entries: [
    {
      algorithm: { name: "dijkstra", family: "graph", implementation: "handwritten" },
      solution_status: "valid",
      metrics: { total_weight: 5, _ops: 4 },
      elapsed_ms_median: 0.1,
      elapsed_ms_p25: 0.1,
      elapsed_ms_p75: 0.1,
      peak_memory_kb: 1.0,
      operation_count: 4,
      hard_violations: 0,
      soft_violations: 0,
      quality_ratio: 1.0,
    },
  ],
  benchmark_id: "abc",
};

describe("benchmark-store", () => {
  beforeEach(() => {
    runBenchmark.mockReset();
    useBenchmarkStore.setState({ result: null, status: "idle", error: null, fetchedAt: null });
  });
  afterEach(() => vi.restoreAllMocks());

  it("stores the result on success", async () => {
    runBenchmark.mockResolvedValueOnce(FAKE);
    await useBenchmarkStore.getState().run({ problem: SAMPLE_ROUTE_PROBLEM });
    expect(useBenchmarkStore.getState().status).toBe("success");
    expect(useBenchmarkStore.getState().result?.benchmark_id).toBe("abc");
  });

  it("records an error message on failure", async () => {
    runBenchmark.mockRejectedValueOnce(new Error("boom"));
    await useBenchmarkStore.getState().run({ problem: SAMPLE_ROUTE_PROBLEM });
    expect(useBenchmarkStore.getState().status).toBe("error");
    expect(useBenchmarkStore.getState().error).toBeTruthy();
  });

  it("skips a second run while the cache is fresh, unless forced", async () => {
    runBenchmark.mockResolvedValue(FAKE);
    await useBenchmarkStore.getState().run({ problem: SAMPLE_ROUTE_PROBLEM });
    await useBenchmarkStore.getState().run({ problem: SAMPLE_ROUTE_PROBLEM });
    expect(runBenchmark).toHaveBeenCalledTimes(1);

    await useBenchmarkStore.getState().run({ problem: SAMPLE_ROUTE_PROBLEM }, { force: true });
    expect(runBenchmark).toHaveBeenCalledTimes(2);
  });

  it("reset clears everything", async () => {
    runBenchmark.mockResolvedValueOnce(FAKE);
    await useBenchmarkStore.getState().run({ problem: SAMPLE_ROUTE_PROBLEM });
    useBenchmarkStore.getState().reset();
    expect(useBenchmarkStore.getState().result).toBeNull();
    expect(useBenchmarkStore.getState().status).toBe("idle");
  });
});
