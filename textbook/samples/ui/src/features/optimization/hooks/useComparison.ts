// DeciTima samples │ 初出 Phase 14
"use client";

import { useComparisonStore } from "../stores/comparison-store";

/**
 * LLM vs Algorithm 比較 store の薄いラッパ。コンポーネントは result / status / run だけ見れば
 * 済む(`useAlgorithmRecommendation` と同じ形。6ドメイン共通 ── problem_type に依存しない)。
 */
export function useComparison() {
  const result = useComparisonStore((s) => s.result);
  const status = useComparisonStore((s) => s.status);
  const error = useComparisonStore((s) => s.error);
  const run = useComparisonStore((s) => s.run);
  const reset = useComparisonStore((s) => s.reset);
  return { result, status, error, run, reset };
}
