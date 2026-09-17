// DeciTima samples │ Phase 11(11-8)
import { apiFetch } from "@/lib/api/client";
import type { StructuringRequest, StructuringResponse } from "@/lib/api/types";

/** POST /api/v1/structure ── 自然言語を OptimizationProblem へ構造化する。 */
export function submitStructuring(request: StructuringRequest): Promise<StructuringResponse> {
  return apiFetch<StructuringResponse>("/api/v1/structure", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
