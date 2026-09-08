// DeciTima samples │ Phase 3
import { apiFetch } from "@/lib/api/client";
import type { BenchmarkRequest, BenchmarkResponse, BenchmarkRunRead } from "@/lib/api/types";

/**
 * POST /api/v1/benchmark ── 1 問題を複数アルゴリズムで解いて実測を並べる。
 * invalid 解でも 200(entries に status="invalid" として含まれる)。
 */
export function runBenchmark(request: BenchmarkRequest): Promise<BenchmarkResponse> {
  return apiFetch<BenchmarkResponse>("/api/v1/benchmark", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/** GET /api/v1/benchmarks/{id} ── 保存済みのベンチマーク実行 1 件。 */
export function getBenchmarkRun(id: string): Promise<BenchmarkRunRead> {
  return apiFetch<BenchmarkRunRead>(`/api/v1/benchmarks/${id}`);
}
