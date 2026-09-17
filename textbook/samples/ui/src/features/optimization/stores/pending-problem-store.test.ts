// DeciTima samples │ Phase 11
// @vitest-environment node
import { beforeEach, describe, expect, it } from "vitest";
import type { OptimizationProblem } from "@/lib/api/types";
import { usePendingProblemStore } from "./pending-problem-store";

const TRAVEL_PROBLEM: OptimizationProblem = {
  problem_type: "travel_planning",
  objectives: [{ sense: "maximize", target: "total_value" }],
  constraints: [],
  data: {
    problem_type: "travel_planning",
    places: [],
    legs: [],
    budget: 1000,
    time_budget: 10,
  },
};

describe("pending-problem-store", () => {
  beforeEach(() => {
    usePendingProblemStore.setState({ pending: null });
  });

  it("consumePending returns null when nothing is pending", () => {
    expect(usePendingProblemStore.getState().consumePending("travel_planning")).toBeNull();
  });

  it("consumePending returns and clears a matching pending problem", () => {
    usePendingProblemStore.getState().setPending(TRAVEL_PROBLEM);

    expect(usePendingProblemStore.getState().consumePending("travel_planning")).toEqual(
      TRAVEL_PROBLEM
    );
    expect(usePendingProblemStore.getState().pending).toBeNull();
  });

  it("consumePending returns null and keeps the problem for a mismatched problem_type", () => {
    usePendingProblemStore.getState().setPending(TRAVEL_PROBLEM);

    expect(usePendingProblemStore.getState().consumePending("route_planning")).toBeNull();
    expect(usePendingProblemStore.getState().pending).toEqual(TRAVEL_PROBLEM);
  });
});
