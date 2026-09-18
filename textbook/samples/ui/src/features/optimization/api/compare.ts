// DeciTima samples │ 初出 Phase 14
import { apiFetch } from "@/lib/api/client";
import type { ComparisonResponse, OptimizationProblem } from "@/lib/api/types";

/**
 * POST /api/v1/compare ── README §14「LLM vs Algorithm Comparison」。同一問題を
 * Algorithm 経路(決定論的に1回)と LLM Only 経路(llmRuns 回再実行)の両方で解き、
 * 6軸(制約遵守率・最適性・再現性・実行時間・エラー率・検証可能性)を比較する。
 * 永続化しない補助機能(recommend/explain と同型)。
 */
export function compareLlmVsAlgorithm(
  problem: OptimizationProblem,
  llmRuns?: number,
): Promise<ComparisonResponse> {
  return apiFetch<ComparisonResponse>("/api/v1/compare", {
    method: "POST",
    body: JSON.stringify({ problem, llm_runs: llmRuns }),
  });
}
