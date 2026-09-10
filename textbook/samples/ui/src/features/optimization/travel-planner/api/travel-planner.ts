// DeciTima samples │ Phase 7
import { apiFetch } from "@/lib/api/client";
import type {
  BenchmarkRequest,
  BenchmarkResponse,
  OptimizationProblem,
  SolveRequest,
  SolveResponse,
} from "@/lib/api/types";

/** POST /api/v1/solve ── 1 アルゴリズムで旅行プランを組む(algorithm 省略で knapsack_dp)。 */
export function solveTravel(
  problem: OptimizationProblem,
  algorithm?: string,
): Promise<SolveResponse> {
  const body: SolveRequest = { problem, algorithm: algorithm ?? null, persist: false };
  return apiFetch<SolveResponse>("/api/v1/solve", { method: "POST", body: JSON.stringify(body) });
}

/** POST /api/v1/benchmark ── Knapsack DP / Greedy / BruteForce を横並びで実測する。 */
export function compareTravel(problem: OptimizationProblem, runs = 5): Promise<BenchmarkResponse> {
  const body: BenchmarkRequest = { problem, runs, persist: false };
  return apiFetch<BenchmarkResponse>("/api/v1/benchmark", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
