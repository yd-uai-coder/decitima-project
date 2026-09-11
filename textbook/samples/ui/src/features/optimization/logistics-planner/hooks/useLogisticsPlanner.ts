// DeciTima samples │ Phase 9
"use client";

import { useLogisticsPlannerStore } from "../stores/logistics-planner-store";

/** logistics-planner store の薄いラッパ(個別セレクタで購読)。 */
export function useLogisticsPlanner() {
  const problem = useLogisticsPlannerStore((s) => s.problem);
  const solution = useLogisticsPlannerStore((s) => s.solution);
  const comparison = useLogisticsPlannerStore((s) => s.comparison);
  const solveStatus = useLogisticsPlannerStore((s) => s.solveStatus);
  const compareStatus = useLogisticsPlannerStore((s) => s.compareStatus);
  const jobId = useLogisticsPlannerStore((s) => s.jobId);
  const jobStatus = useLogisticsPlannerStore((s) => s.jobStatus);
  const error = useLogisticsPlannerStore((s) => s.error);
  const setProblem = useLogisticsPlannerStore((s) => s.setProblem);
  const solve = useLogisticsPlannerStore((s) => s.solve);
  const compare = useLogisticsPlannerStore((s) => s.compare);
  const submitAsJob = useLogisticsPlannerStore((s) => s.submitAsJob);
  const reset = useLogisticsPlannerStore((s) => s.reset);
  return {
    problem,
    solution,
    comparison,
    solveStatus,
    compareStatus,
    jobId,
    jobStatus,
    error,
    setProblem,
    solve,
    compare,
    submitAsJob,
    reset,
  };
}
