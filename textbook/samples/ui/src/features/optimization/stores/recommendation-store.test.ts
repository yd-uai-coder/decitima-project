// DeciTima samples │ 初出 Phase 12
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { RecommendationResponse } from "@/lib/api/types";
import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";

const recommendAlgorithm = vi.fn();
vi.mock("../api/recommend", () => ({
  recommendAlgorithm: (...a: unknown[]) => recommendAlgorithm(...a),
}));

import { useRecommendationStore } from "./recommendation-store";

const FAKE: RecommendationResponse = {
  problem_type: "route_planning",
  rule_preferred: "dijkstra",
  recommendations: [
    {
      name: "dijkstra",
      family: "graph",
      implementation: "handwritten",
      description: "非負辺の単一始点最短路。",
      is_rule_preferred: true,
      llm_rank: 1,
      llm_comment: "この問題では既定のままでよい",
    },
  ],
  notes: [],
};

describe("recommendation-store", () => {
  beforeEach(() => {
    recommendAlgorithm.mockReset();
    useRecommendationStore.setState({ result: null, status: "idle", error: null, fetchedAt: null });
  });
  afterEach(() => vi.restoreAllMocks());

  it("stores the result on success", async () => {
    recommendAlgorithm.mockResolvedValueOnce(FAKE);
    await useRecommendationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(useRecommendationStore.getState().status).toBe("success");
    expect(useRecommendationStore.getState().result?.rule_preferred).toBe("dijkstra");
  });

  it("records an error message on failure", async () => {
    recommendAlgorithm.mockRejectedValueOnce(new Error("boom"));
    await useRecommendationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(useRecommendationStore.getState().status).toBe("error");
    expect(useRecommendationStore.getState().error).toBeTruthy();
  });

  it("skips a second run while the cache is fresh, unless forced", async () => {
    recommendAlgorithm.mockResolvedValue(FAKE);
    await useRecommendationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    await useRecommendationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    expect(recommendAlgorithm).toHaveBeenCalledTimes(1);

    await useRecommendationStore.getState().run(SAMPLE_ROUTE_PROBLEM, { force: true });
    expect(recommendAlgorithm).toHaveBeenCalledTimes(2);
  });

  it("reset clears everything", async () => {
    recommendAlgorithm.mockResolvedValueOnce(FAKE);
    await useRecommendationStore.getState().run(SAMPLE_ROUTE_PROBLEM);
    useRecommendationStore.getState().reset();
    expect(useRecommendationStore.getState().result).toBeNull();
    expect(useRecommendationStore.getState().status).toBe("idle");
  });
});
