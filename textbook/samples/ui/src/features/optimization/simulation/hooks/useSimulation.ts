// DeciTima samples │ Phase 10
"use client";

import { useJobPolling } from "../../hooks/useJobPolling";
import { useSimulationStore } from "../stores/simulation-store";

/**
 * シミュレーション画面が要る状態を1つに束ねる。投入は `simulation-store`(Phase 10)、
 * 結果のポーリングは既存の `useJobPolling`(problem_type に依存しない共通フック、Phase 9-9)
 * をそのまま再利用する ── ジョブキューを再利用したバックエンド設計(Phase 10-4)と対応する。
 */
export function useSimulation() {
  const store = useSimulationStore();
  const { job, error: pollError } = useJobPolling(store.jobId);

  return {
    ...store,
    job,
    pollError,
  };
}
