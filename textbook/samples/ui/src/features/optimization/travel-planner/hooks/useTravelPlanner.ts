// DeciTima samples │ Phase 7
"use client";

import { useTravelPlannerStore } from "../stores/travel-planner-store";

/** travel-planner store の薄いラッパ(個別セレクタで購読)。 */
export function useTravelPlanner() {
  const problem = useTravelPlannerStore((s) => s.problem);
  const solution = useTravelPlannerStore((s) => s.solution);
  const comparison = useTravelPlannerStore((s) => s.comparison);
  const solveStatus = useTravelPlannerStore((s) => s.solveStatus);
  const compareStatus = useTravelPlannerStore((s) => s.compareStatus);
  const error = useTravelPlannerStore((s) => s.error);
  const setProblem = useTravelPlannerStore((s) => s.setProblem);
  const solve = useTravelPlannerStore((s) => s.solve);
  const compare = useTravelPlannerStore((s) => s.compare);
  const reset = useTravelPlannerStore((s) => s.reset);
  return {
    problem,
    solution,
    comparison,
    solveStatus,
    compareStatus,
    error,
    setProblem,
    solve,
    compare,
    reset,
  };
}
