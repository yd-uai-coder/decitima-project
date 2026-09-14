// DeciTima samples │ Phase 10
import { apiFetch } from "@/lib/api/client";
import type { JobSubmitResponse, SimulationRequest } from "@/lib/api/types";

/**
 * POST /api/v1/simulate ── base problem + シナリオ群を非同期ジョブとして投入する。
 * 結果のポーリングは既存の `getJobStatus`(`../../api/jobs`、Phase 9-8)を再利用する ──
 * 専用の GET は無い(バックエンドが同じ jobs テーブルを再利用しているため、Phase 10-4)。
 */
export function submitSimulation(request: SimulationRequest): Promise<JobSubmitResponse> {
  return apiFetch<JobSubmitResponse>("/api/v1/simulate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
