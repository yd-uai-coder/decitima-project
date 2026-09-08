// DeciTima samples │ Phase 5
import { apiFetch } from "@/lib/api/client";
import type {
  BenchmarkRequest,
  BenchmarkResponse,
  OptimizationProblem,
  SolveRequest,
  SolveResponse,
} from "@/lib/api/types";

/** POST /api/v1/solve ── 1 アルゴリズムで MST を解く(algorithm 省略で kruskal)。 */
export function solveNetwork(
  problem: OptimizationProblem,
  algorithm?: string,
): Promise<SolveResponse> {
  const body: SolveRequest = { problem, algorithm: algorithm ?? null, persist: false };
  return apiFetch<SolveResponse>("/api/v1/solve", { method: "POST", body: JSON.stringify(body) });
}

/** POST /api/v1/benchmark ── Kruskal / Prim / networkx を横並びで実測する。 */
export function compareNetwork(problem: OptimizationProblem, runs = 5): Promise<BenchmarkResponse> {
  const body: BenchmarkRequest = { problem, runs, persist: false };
  return apiFetch<BenchmarkResponse>("/api/v1/benchmark", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
