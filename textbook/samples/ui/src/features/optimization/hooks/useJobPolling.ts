// DeciTima samples │ Phase 9
"use client";

import { useEffect, useState } from "react";
import { getJobStatus } from "@/features/optimization/api/jobs";
import { ApiError } from "@/lib/api/client";
import type { JobStatusResponse } from "@/lib/api/types";

const POLL_INTERVAL_MS = 1500;

/**
 * ジョブ id を渡すと succeeded/failed になるまで GET /api/v1/jobs/{id} を定期的に叩く。
 * problem_type に依存しない共通フック(バックエンドのジョブキューが横断インフラなのと対応 ──
 * Phase 9-8)。jobId が null の間、および succeeded/failed に達した後はポーリングしない。
 */
export function useJobPolling(jobId: string | null): {
  job: JobStatusResponse | null;
  error: string | null;
} {
  const [trackedJobId, setTrackedJobId] = useState(jobId);
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // jobId が変わったら job/error をリセットする ── レンダー中に行う(React 公式の
  // 「prop の変化に応じて state を調整する」パターン)。effect 内で同期的に setState すると
  // カスケードレンダーを招くため避ける(react-hooks/set-state-in-effect)。
  if (jobId !== trackedJobId) {
    setTrackedJobId(jobId);
    setJob(null);
    setError(null);
  }

  useEffect(() => {
    if (!jobId) return;

    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | null = null;

    const tick = async () => {
      try {
        const res = await getJobStatus(jobId);
        if (cancelled) return;
        setJob(res);
        if ((res.status === "succeeded" || res.status === "failed") && timer) {
          clearInterval(timer);
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "ジョブ状態の取得に失敗しました");
        if (timer) clearInterval(timer);
      }
    };

    void tick(); // 即座に1回
    timer = setInterval(() => void tick(), POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [jobId]);

  return { job, error };
}
