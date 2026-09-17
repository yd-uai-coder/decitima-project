// DeciTima samples │ 初出 Phase 12
import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import { isCacheFresh } from "@/lib/api/cache";
import type { AsyncStatus, OptimizationProblem, RecommendationResponse } from "@/lib/api/types";
import { recommendAlgorithm } from "../api/recommend";

type RecommendationStore = {
  result: RecommendationResponse | null;
  status: AsyncStatus;
  error: string | null;
  fetchedAt: number | null;
  // run: 推薦を取得して結果を保持する。直近の成功が TTL 内なら再実行しない
  // (force で無視できる ── benchmark-store と同じキャッシュ方針)。
  run: (problem: OptimizationProblem, options?: { force?: boolean }) => Promise<void>;
  reset: () => void;
};

export const useRecommendationStore = create<RecommendationStore>((set, get) => ({
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
      const result = await recommendAlgorithm(problem);
      set({ result, status: "success", error: null, fetchedAt: Date.now() });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "アルゴリズム推薦に失敗しました";
      set({ status: "error", error: message });
    }
  },
  reset: () => set({ result: null, status: "idle", error: null, fetchedAt: null }),
}));
