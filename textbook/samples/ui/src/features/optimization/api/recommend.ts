// DeciTima samples │ 初出 Phase 12
import { apiFetch } from "@/lib/api/client";
import type { OptimizationProblem, RecommendationResponse } from "@/lib/api/types";

/**
 * POST /api/v1/algorithms/recommend ── 構造化済み問題に対し、候補アルゴリズムと
 * 推薦理由(ルール + LLM)を返す。/solve の既定選択には影響しない(opt-in)。
 */
export function recommendAlgorithm(
  problem: OptimizationProblem,
): Promise<RecommendationResponse> {
  return apiFetch<RecommendationResponse>("/api/v1/algorithms/recommend", {
    method: "POST",
    body: JSON.stringify({ problem }),
  });
}
