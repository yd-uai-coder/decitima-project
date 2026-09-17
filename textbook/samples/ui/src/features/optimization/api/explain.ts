// DeciTima samples │ 初出 Phase 13
import { apiFetch } from "@/lib/api/client";
import type { ExplanationResponse } from "@/lib/api/types";

/**
 * POST /api/v1/solutions/{solution_id}/explain ── 保存済みの解を自然言語で説明する。
 * README §13「なぜこの解か / どの制約が重要か / どのアルゴリズムか / 他候補との違い /
 * 改善余地」を返す(補助機能、永続化しない)。
 */
export function explainSolution(solutionId: string): Promise<ExplanationResponse> {
  return apiFetch<ExplanationResponse>(`/api/v1/solutions/${solutionId}/explain`, {
    method: "POST",
  });
}
