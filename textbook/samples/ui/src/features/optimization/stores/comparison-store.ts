// DeciTima samples │ 初出 Phase 14
import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import { isCacheFresh } from "@/lib/api/cache";
import type { AsyncStatus, ComparisonResponse, OptimizationProblem } from "@/lib/api/types";
import { compareLlmVsAlgorithm } from "../api/compare";

type ComparisonStore = {
  result: ComparisonResponse | null;
  status: AsyncStatus;
  error: string | null;
  fetchedAt: number | null;
  // run: 比較を実行して結果を保持する。直近の成功が TTL 内なら再実行しない
  // (force で無視できる ── recommendation-store と同じキャッシュ方針)。
  run: (
    problem: OptimizationProblem,
    options?: { llmRuns?: number; force?: boolean },
  ) => Promise<void>;
  reset: () => void;
};

export const useComparisonStore = create<ComparisonStore>((set, get) => ({
  result: null,
  status: "idle",
  error: null,
  fetchedAt: null,
  run: async (problem, options) => {
    if (!options?.force && get().status === "success" && isCacheFresh(get().fetchedAt)) {
      return;
    }
    set({ status: "loading", error: null });
    try {
      const result = await compareLlmVsAlgorithm(problem, options?.llmRuns);
      set({ result, status: "success", error: null, fetchedAt: Date.now() });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "LLM比較の実行に失敗しました";
      set({ status: "error", error: message });
    }
  },
  reset: () => set({ result: null, status: "idle", error: null, fetchedAt: null }),
}));
