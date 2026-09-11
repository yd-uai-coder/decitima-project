// DeciTima samples │ Phase 9
import { create } from "zustand";
import { submitJob } from "@/features/optimization/api/jobs";
import { ApiError } from "@/lib/api/client";
import type {
  AsyncStatus,
  BenchmarkResponse,
  CandidateSolution,
  OptimizationProblem,
} from "@/lib/api/types";
import { compareLogistics, solveLogistics } from "../api/logistics-planner";
import { LOGISTICS_SAMPLES } from "../sample-problems";

type LogisticsPlannerStore = {
  problem: OptimizationProblem;
  solution: CandidateSolution | null;
  comparison: BenchmarkResponse | null;
  solveStatus: AsyncStatus;
  compareStatus: AsyncStatus;
  error: string | null;
  // ジョブキュー(/jobs)経由の非同期実行。実際の結果のポーリングは useJobPolling(コンポーネント側)
  // が担い、ストアは「投入した job_id」だけを覚える(進行中の状態をストアに持たせない設計)。
  jobId: string | null;
  jobStatus: AsyncStatus;
  setProblem: (problem: OptimizationProblem) => void;
  solve: (algorithm?: string) => Promise<void>;
  compare: () => Promise<void>;
  submitAsJob: (algorithm?: string) => Promise<void>;
  reset: () => void;
};

export const useLogisticsPlannerStore = create<LogisticsPlannerStore>((set, get) => ({
  problem: LOGISTICS_SAMPLES[0].problem,
  solution: null,
  comparison: null,
  solveStatus: "idle",
  compareStatus: "idle",
  error: null,
  jobId: null,
  jobStatus: "idle",
  setProblem: (problem) =>
    set({ problem, solution: null, comparison: null, jobId: null, error: null }),
  solve: async (algorithm) => {
    set({ solveStatus: "loading", error: null });
    try {
      const res = await solveLogistics(get().problem, algorithm);
      set({ solution: res.solution, solveStatus: "success" });
    } catch (err) {
      set({ solveStatus: "error", error: _message(err, "配送計画の計算に失敗しました") });
    }
  },
  compare: async () => {
    set({ compareStatus: "loading", error: null });
    try {
      const res = await compareLogistics(get().problem);
      set({ comparison: res, compareStatus: "success" });
    } catch (err) {
      set({ compareStatus: "error", error: _message(err, "比較に失敗しました") });
    }
  },
  submitAsJob: async (algorithm) => {
    set({ jobStatus: "loading", error: null, jobId: null });
    try {
      const res = await submitJob(get().problem, algorithm);
      set({ jobId: res.job_id, jobStatus: "success" });
    } catch (err) {
      set({ jobStatus: "error", error: _message(err, "ジョブの投入に失敗しました") });
    }
  },
  reset: () =>
    set({
      problem: LOGISTICS_SAMPLES[0].problem,
      solution: null,
      comparison: null,
      solveStatus: "idle",
      compareStatus: "idle",
      jobId: null,
      jobStatus: "idle",
      error: null,
    }),
}));

function _message(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}
