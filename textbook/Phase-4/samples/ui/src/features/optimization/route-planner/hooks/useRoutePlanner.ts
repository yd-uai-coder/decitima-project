"use client";

import { useRoutePlannerStore } from "../stores/route-planner-store";

/**
 * route-planner store の薄いラッパ。個別セレクタで購読する
 * (オブジェクトリテラルを返すと毎レンダー参照が変わり再描画ループになるため)。
 */
export function useRoutePlanner() {
  const problem = useRoutePlannerStore((s) => s.problem);
  const solution = useRoutePlannerStore((s) => s.solution);
  const comparison = useRoutePlannerStore((s) => s.comparison);
  const solveStatus = useRoutePlannerStore((s) => s.solveStatus);
  const compareStatus = useRoutePlannerStore((s) => s.compareStatus);
  const error = useRoutePlannerStore((s) => s.error);
  const setProblem = useRoutePlannerStore((s) => s.setProblem);
  const solve = useRoutePlannerStore((s) => s.solve);
  const compare = useRoutePlannerStore((s) => s.compare);
  const reset = useRoutePlannerStore((s) => s.reset);
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
