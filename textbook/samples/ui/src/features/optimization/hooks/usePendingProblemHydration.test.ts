// DeciTima samples │ Phase 11
// @vitest-environment jsdom
import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { OptimizationProblem } from "@/lib/api/types";
import { usePendingProblemStore } from "../stores/pending-problem-store";
import { usePendingProblemHydration } from "./usePendingProblemHydration";

const ROUTE_PROBLEM: OptimizationProblem = {
  problem_type: "route_planning",
  objectives: [{ sense: "minimize", target: "total_weight" }],
  constraints: [],
  data: { problem_type: "route_planning", nodes: [], edges: [], start: "A", goal: "B" },
};

describe("usePendingProblemHydration", () => {
  beforeEach(() => {
    usePendingProblemStore.setState({ pending: null });
  });

  it("does nothing when there is no pending problem", () => {
    const setProblem = vi.fn();
    renderHook(() => usePendingProblemHydration("route_planning", setProblem));
    expect(setProblem).not.toHaveBeenCalled();
  });

  it("applies a pending problem that matches the page's problem_type", () => {
    usePendingProblemStore.getState().setPending(ROUTE_PROBLEM);
    const setProblem = vi.fn();

    renderHook(() => usePendingProblemHydration("route_planning", setProblem));

    expect(setProblem).toHaveBeenCalledWith(ROUTE_PROBLEM);
    expect(usePendingProblemStore.getState().pending).toBeNull(); // 消費済み
  });

  it("ignores a pending problem meant for a different problem_type", () => {
    usePendingProblemStore.getState().setPending(ROUTE_PROBLEM);
    const setProblem = vi.fn();

    renderHook(() => usePendingProblemHydration("travel_planning", setProblem));

    expect(setProblem).not.toHaveBeenCalled();
    expect(usePendingProblemStore.getState().pending).toEqual(ROUTE_PROBLEM); // 消費されない
  });
});
