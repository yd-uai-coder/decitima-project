// DeciTima samples │ Phase 11
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const submitStructuring = vi.fn();
vi.mock("../api/structure", () => ({
  submitStructuring: (...a: unknown[]) => submitStructuring(...a),
}));

import type { OptimizationProblem } from "@/lib/api/types";
import { useStructuringStore } from "./structuring-store";

const ROUTE_PROBLEM: OptimizationProblem = {
  problem_type: "route_planning",
  objectives: [{ sense: "minimize", target: "total_weight" }],
  constraints: [],
  data: { problem_type: "route_planning", nodes: [], edges: [], start: "A", goal: "B" },
};

describe("structuring-store", () => {
  beforeEach(() => {
    submitStructuring.mockReset();
    useStructuringStore.getState().reset();
  });
  afterEach(() => vi.restoreAllMocks());

  it("submit stores the returned problem/conversation/notes", async () => {
    submitStructuring.mockResolvedValueOnce({
      conversation_id: "conv-1",
      problem_type: "route_planning",
      problem: ROUTE_PROBLEM,
      notes: ["note"],
    });
    useStructuringStore.getState().setText("Aから Bまで行きたい");

    await useStructuringStore.getState().submit();

    expect(useStructuringStore.getState().problem).toEqual(ROUTE_PROBLEM);
    expect(useStructuringStore.getState().conversationId).toBe("conv-1");
    expect(useStructuringStore.getState().notes).toEqual(["note"]);
    expect(useStructuringStore.getState().status).toBe("success");
  });

  it("records an error on failure", async () => {
    submitStructuring.mockRejectedValueOnce(new Error("boom"));
    await useStructuringStore.getState().submit();
    expect(useStructuringStore.getState().status).toBe("error");
    expect(useStructuringStore.getState().problem).toBeNull();
  });

  it("setProblem updates the local problem without calling the API again", () => {
    useStructuringStore.setState({ problem: ROUTE_PROBLEM });
    const edited: OptimizationProblem = { ...ROUTE_PROBLEM, objectives: [] };

    useStructuringStore.getState().setProblem(edited);

    expect(useStructuringStore.getState().problem).toEqual(edited);
    expect(submitStructuring).not.toHaveBeenCalled();
  });
});
