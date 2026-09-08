// DeciTima samples │ Phase 3
import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import { isCacheFresh } from "@/lib/api/cache";
import type { AsyncStatus, BenchmarkRequest, BenchmarkResponse } from "@/lib/api/types";
import { runBenchmark } from "../api/benchmark";

type BenchmarkStore = {
  result: BenchmarkResponse | null;
  status: AsyncStatus;
  error: string | null;
  fetchedAt: number | null;
  // run: ベンチマークを実行して結果を保持する。直近の成功が TTL 内なら再実行しない
  // (force で無視できる。React Query は使わず fetchedAt + isCacheFresh で鮮度管理)。
  run: (request: BenchmarkRequest, options?: { force?: boolean }) => Promise<void>;
  reset: () => void;
};

export const useBenchmarkStore = create<BenchmarkStore>((set, get) => ({
  result: null,
  status: "idle",
  error: null,
  fetchedAt: null,
  run: async (request, options) => {
    if (!options?.force && get().status === "success" && isCacheFresh(get().fetchedAt)) {
      return;
    }
    set({ status: "loading", error: null });
    try {
      const result = await runBenchmark(request);
      set({ result, status: "success", error: null, fetchedAt: Date.now() });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "ベンチマークに失敗しました";
      set({ status: "error", error: message });
    }
  },
  reset: () => set({ result: null, status: "idle", error: null, fetchedAt: null }),
}));
