// DeciTima samples │ 初出 Phase 13
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ExplanationResponse } from "@/lib/api/types";
import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";

const explainSolution = vi.fn();
vi.mock("../api/explain", () => ({
  explainSolution: (...a: unknown[]) => explainSolution(...a),
}));
const persistSolve = vi.fn();
vi.mock("../api/solve", () => ({
  persistSolve: (...a: unknown[]) => persistSolve(...a),
}));

import { useExplanationStore } from "./explanation-store";

const FAKE: ExplanationResponse = {
  solution_id: "s1",
  problem_type: "route_planning",
  algorithm_name: "dijkstra",
  why_this_solution: "最短経路です",
  key_constraints: "C を必ず経由する制約が効いています",
  algorithm_rationale: "非負辺なので dijkstra です",
  alternatives_comparison: "bellman_ford は今回不要です",
  improvement_notes: "改善余地はありません",
  notes: [],
};

describe("explanation-store", () => {
  beforeEach(() => {
    explainSolution.mockReset();
    persistSolve.mockReset();
    persistSolve.mockResolvedValue({
      solution: { status: "valid", assignments: {}, metrics: {}, violations: [], produced_by: {} },
      problem_id: "p1",
      solution_id: "s1",
    });
    useExplanationStore.setState({ result: null, status: "idle", error: null, fetchedAt: null });
  });
  afterEach(() => vi.restoreAllMocks());

  it("solves (persist) then explains, storing the result on success", async () => {
    explainSolution.mockResolvedValueOnce(FAKE);
    await useExplanationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(persistSolve).toHaveBeenCalledWith(SAMPLE_ROUTE_PROBLEM, undefined);
    expect(explainSolution).toHaveBeenCalledWith("s1");
    expect(useExplanationStore.getState().status).toBe("success");
    expect(useExplanationStore.getState().result?.algorithm_name).toBe("dijkstra");
  });

  it("records an error message when solve fails to persist", async () => {
    persistSolve.mockResolvedValueOnce({
      solution: { status: "valid", assignments: {}, metrics: {}, violations: [], produced_by: {} },
      problem_id: null,
      solution_id: null,
    });
    await useExplanationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(useExplanationStore.getState().status).toBe("error");
    expect(explainSolution).not.toHaveBeenCalled();
  });

  it("records an error message when explain fails", async () => {
    explainSolution.mockRejectedValueOnce(new Error("boom"));
    await useExplanationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(useExplanationStore.getState().status).toBe("error");
    expect(useExplanationStore.getState().error).toBeTruthy();
  });

  it("skips a second run while the cache is fresh, unless forced", async () => {
    explainSolution.mockResolvedValue(FAKE);
    await useExplanationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    await useExplanationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(explainSolution).toHaveBeenCalledTimes(1);

    await useExplanationStore.getState().run(SAMPLE_ROUTE_PROBLEM, { force: true });
    expect(explainSolution).toHaveBeenCalledTimes(2);
  });

  it("reset clears everything", async () => {
    explainSolution.mockResolvedValueOnce(FAKE);
    await useExplanationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    useExplanationStore.getState().reset();
    expect(useExplanationStore.getState().result).toBeNull();
    expect(useExplanationStore.getState().status).toBe("idle");
  });
});
