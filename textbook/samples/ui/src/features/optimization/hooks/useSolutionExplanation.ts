// DeciTima samples │ 初出 Phase 13
"use client";

import { useExplanationStore } from "../stores/explanation-store";

/**
 * 解の説明(Result Explanation)store の薄いラッパ。コンポーネントは result / status / run
 * だけ見れば済む(`useAlgorithmRecommendation` と同じ形。6ドメイン共通 ──
 * problem_type に依存しない)。
 */
export function useSolutionExplanation() {
  const result = useExplanationStore((s) => s.result);
  const status = useExplanationStore((s) => s.status);
  const error = useExplanationStore((s) => s.error);
  const run = useExplanationStore((s) => s.run);
  const reset = useExplanationStore((s) => s.reset);
  return { result, status, error, run, reset };
}
