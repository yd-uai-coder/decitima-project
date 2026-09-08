// DeciTima samples │ Phase 4
import { apiFetch } from "@/lib/api/client";
import type {
  BenchmarkRequest,
  BenchmarkResponse,
  OptimizationProblem,
  SolveRequest,
  SolveResponse,
} from "@/lib/api/types";

/**
 * POST /api/v1/solve ── 1 アルゴリズムで解いて「経路つき」の検証済み解を返す。
 * algorithm を省くと backend が rule-based に選ぶ(負辺→Bellman-Ford / 座標→A* / 既定→Dijkstra)。
 */
export function solveRoute(
  problem: OptimizationProblem,
  algorithm?: string,
): Promise<SolveResponse> {
  const body: SolveRequest = { problem, algorithm: algorithm ?? null, persist: false };
  return apiFetch<SolveResponse>("/api/v1/solve", { method: "POST", body: JSON.stringify(body) });
}

/** POST /api/v1/benchmark ── registry の全 route アルゴリズムを横並びで実測する。 */
export function compareRoute(problem: OptimizationProblem, runs = 5): Promise<BenchmarkResponse> {
  const body: BenchmarkRequest = { problem, runs, persist: false };
  return apiFetch<BenchmarkResponse>("/api/v1/benchmark", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
