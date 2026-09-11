// DeciTima samples │ Phase 9
import { apiFetch } from "@/lib/api/client";
import type { JobStatusResponse, JobSubmitResponse, OptimizationProblem } from "@/lib/api/types";

/** POST /api/v1/jobs ── 重い solve をジョブとして投入する(problem_type に依存しない共通 API)。 */
export function submitJob(
  problem: OptimizationProblem,
  algorithm?: string,
): Promise<JobSubmitResponse> {
  return apiFetch<JobSubmitResponse>("/api/v1/jobs", {
    method: "POST",
    body: JSON.stringify({ problem, algorithm: algorithm ?? null, persist: true }),
  });
}

/** GET /api/v1/jobs/{id} ── ジョブの状態・結果をポーリングする。 */
export function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return apiFetch<JobStatusResponse>(`/api/v1/jobs/${jobId}`);
}
