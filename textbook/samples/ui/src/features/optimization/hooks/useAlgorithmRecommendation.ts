// DeciTima samples │ 初出 Phase 12
"use client";

import { useRecommendationStore } from "../stores/recommendation-store";

/**
 * アルゴリズム推薦 store の薄いラッパ。コンポーネントは result / status / run だけ見れば済む
 * (`useBenchmark` と同じ形。6ドメイン共通 ── problem_type に依存しない)。
 */
export function useAlgorithmRecommendation() {
  const result = useRecommendationStore((s) => s.result);
  const status = useRecommendationStore((s) => s.status);
  const error = useRecommendationStore((s) => s.error);
  const run = useRecommendationStore((s) => s.run);
  const reset = useRecommendationStore((s) => s.reset);
  return { result, status, error, run, reset };
}
