"use client";

import { useProjectPlannerStore } from "../stores/project-planner-store";

/** project-planner store の薄いラッパ(個別セレクタで購読)。 */
export function useProjectPlanner() {
  const problem = useProjectPlannerStore((s) => s.problem);
  const solution = useProjectPlannerStore((s) => s.solution);
  const comparison = useProjectPlannerStore((s) => s.comparison);
  const solveStatus = useProjectPlannerStore((s) => s.solveStatus);
  const compareStatus = useProjectPlannerStore((s) => s.compareStatus);
  const error = useProjectPlannerStore((s) => s.error);
  const setProblem = useProjectPlannerStore((s) => s.setProblem);
  const solve = useProjectPlannerStore((s) => s.solve);
  const compare = useProjectPlannerStore((s) => s.compare);
  const reset = useProjectPlannerStore((s) => s.reset);
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
