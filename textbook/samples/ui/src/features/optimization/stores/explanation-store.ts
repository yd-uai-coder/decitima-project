// DeciTima samples │ 初出 Phase 13
import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import { isCacheFresh } from "@/lib/api/cache";
import type { AsyncStatus, ExplanationResponse, OptimizationProblem } from "@/lib/api/types";
import { explainSolution } from "../api/explain";
import { persistSolve } from "../api/solve";

type ExplanationStore = {
  result: ExplanationResponse | null;
  status: AsyncStatus;
  error: string | null;
  fetchedAt: number | null;
  // run: 現在の問題を永続化つきで solve し、その solution_id を使って説明を取得する
  // (`recommendation-store` と同じキャッシュ方針 ── 直近の成功が TTL 内なら再実行しない)。
  run: (
    problem: OptimizationProblem,
    options?: { algorithm?: string; force?: boolean },
  ) => Promise<void>;
  reset: () => void;
};

export const useExplanationStore = create<ExplanationStore>((set, get) => ({
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
      const solved = await persistSolve(problem, options?.algorithm);
      if (!solved.solution_id) {
        throw new ApiError(500, "解が永続化されませんでした");
      }
      const result = await explainSolution(solved.solution_id);
      set({ result, status: "success", error: null, fetchedAt: Date.now() });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "解の説明生成に失敗しました";
      set({ status: "error", error: message });
    }
  },
  reset: () => set({ result: null, status: "idle", error: null, fetchedAt: null }),
}));
