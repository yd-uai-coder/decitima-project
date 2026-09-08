// DeciTima samples │ Phase 6
"use client";

import { useShiftSchedulerStore } from "../stores/shift-scheduler-store";

/** shift-scheduler store の薄いラッパ(個別セレクタで購読)。 */
export function useShiftScheduler() {
  const problem = useShiftSchedulerStore((s) => s.problem);
  const solution = useShiftSchedulerStore((s) => s.solution);
  const comparison = useShiftSchedulerStore((s) => s.comparison);
  const solveStatus = useShiftSchedulerStore((s) => s.solveStatus);
  const compareStatus = useShiftSchedulerStore((s) => s.compareStatus);
  const error = useShiftSchedulerStore((s) => s.error);
  const setProblem = useShiftSchedulerStore((s) => s.setProblem);
  const solve = useShiftSchedulerStore((s) => s.solve);
  const compare = useShiftSchedulerStore((s) => s.compare);
  const reset = useShiftSchedulerStore((s) => s.reset);
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
