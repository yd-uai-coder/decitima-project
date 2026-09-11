// DeciTima samples │ Phase 9
import { apiFetch } from "@/lib/api/client";
import type {
  BenchmarkRequest,
  BenchmarkResponse,
  OptimizationProblem,
  SolveRequest,
  SolveResponse,
} from "@/lib/api/types";

/** POST /api/v1/solve ── 1 アルゴリズムで配送計画を解く(algorithm 省略で select_strategy 任せ)。 */
export function solveLogistics(
  problem: OptimizationProblem,
  algorithm?: string,
): Promise<SolveResponse> {
  const body: SolveRequest = { problem, algorithm: algorithm ?? null, persist: false };
  return apiFetch<SolveResponse>("/api/v1/solve", { method: "POST", body: JSON.stringify(body) });
}

/** POST /api/v1/benchmark ── 5 strategy(knapsack_dp/greedy/branch_and_bound/brute_force/pulp_milp)
 * を横並びで実測する。 */
export function compareLogistics(
  problem: OptimizationProblem,
  runs = 5,
): Promise<BenchmarkResponse> {
  const body: BenchmarkRequest = { problem, runs, persist: false };
  return apiFetch<BenchmarkResponse>("/api/v1/benchmark", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
