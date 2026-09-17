// DeciTima samples │ Phase 11(11-8)
"use client";

import { useEffect } from "react";
import type { OptimizationProblem } from "@/lib/api/types";
import { usePendingProblemStore } from "../stores/pending-problem-store";

/**
 * ドメインページのマウント時に、Structuring 画面(README §11)から渡された保留中の問題が
 * あればそのページの store に流し込む(無ければ何もせず、既存のサンプル問題のまま)。
 * problem_type に依存しない共通フック(`useJobPolling` と同じ設計方針、Phase 9-9)。
 */
export function usePendingProblemHydration(
  problemType: OptimizationProblem["problem_type"],
  setProblem: (problem: OptimizationProblem) => void
): void {
  const consumePending = usePendingProblemStore((s) => s.consumePending);

  useEffect(() => {
    const pending = consumePending(problemType);
    if (pending) setProblem(pending);
  }, [problemType, consumePending, setProblem]);
}
