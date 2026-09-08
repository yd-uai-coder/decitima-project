import { apiFetch } from "@/lib/api/client";
import type {
  BenchmarkRequest,
  BenchmarkResponse,
  OptimizationProblem,
  SolveRequest,
  SolveResponse,
} from "@/lib/api/types";

/** POST /api/v1/solve ── 1 アルゴリズムでシフトを解く(algorithm 省略で backtracking)。 */
export function solveShift(
  problem: OptimizationProblem,
  algorithm?: string,
): Promise<SolveResponse> {
  const body: SolveRequest = { problem, algorithm: algorithm ?? null, persist: false };
  return apiFetch<SolveResponse>("/api/v1/solve", { method: "POST", body: JSON.stringify(body) });
}

/** POST /api/v1/benchmark ── Greedy / Backtracking / B&B / CP-SAT を横並びで実測する。 */
export function compareShift(problem: OptimizationProblem, runs = 5): Promise<BenchmarkResponse> {
  const body: BenchmarkRequest = { problem, runs, persist: false };
  return apiFetch<BenchmarkResponse>("/api/v1/benchmark", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
