// DeciTima samples │ Phase 5
"use client";

import { useNetworkDesignerStore } from "../stores/network-designer-store";

/** network-designer store の薄いラッパ(個別セレクタで購読)。 */
export function useNetworkDesigner() {
  const problem = useNetworkDesignerStore((s) => s.problem);
  const solution = useNetworkDesignerStore((s) => s.solution);
  const comparison = useNetworkDesignerStore((s) => s.comparison);
  const solveStatus = useNetworkDesignerStore((s) => s.solveStatus);
  const compareStatus = useNetworkDesignerStore((s) => s.compareStatus);
  const error = useNetworkDesignerStore((s) => s.error);
  const setProblem = useNetworkDesignerStore((s) => s.setProblem);
  const solve = useNetworkDesignerStore((s) => s.solve);
  const compare = useNetworkDesignerStore((s) => s.compare);
  const reset = useNetworkDesignerStore((s) => s.reset);
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
