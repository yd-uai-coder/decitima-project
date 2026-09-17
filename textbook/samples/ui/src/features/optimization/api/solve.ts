// DeciTima samples │ 初出 Phase 13
import { apiFetch } from "@/lib/api/client";
import type { OptimizationProblem, SolveResponse } from "@/lib/api/types";

/**
 * POST /api/v1/solve(persist: true)。
 *
 * 各ドメインパネルの「解く」(`solveRoute` 等、`persist: false` ── 編集中の探索的な試行を
 * DB に残さないための既存方針)とは別に、`ExplanationCard` が説明対象の解を確定させるための
 * 永続化つき solve をここに用意する(problem_type に依存しない共通ヘルパ ── `recommend.ts` と
 * 同じ置き場所の考え方)。
 */
export function persistSolve(
  problem: OptimizationProblem,
  algorithm?: string,
): Promise<SolveResponse> {
  const body = { problem, algorithm: algorithm ?? null, persist: true };
  return apiFetch<SolveResponse>("/api/v1/solve", { method: "POST", body: JSON.stringify(body) });
}
