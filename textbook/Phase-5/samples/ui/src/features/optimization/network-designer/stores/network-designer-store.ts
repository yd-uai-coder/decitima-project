import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import type {
  AsyncStatus,
  BenchmarkResponse,
  CandidateSolution,
  OptimizationProblem,
} from "@/lib/api/types";
import { compareNetwork, solveNetwork } from "../api/network-designer";
import { NETWORK_SAMPLES } from "../sample-problems";

type NetworkDesignerStore = {
  problem: OptimizationProblem;
  solution: CandidateSolution | null;
  comparison: BenchmarkResponse | null;
  solveStatus: AsyncStatus;
  compareStatus: AsyncStatus;
  error: string | null;
  setProblem: (problem: OptimizationProblem) => void;
  solve: (algorithm?: string) => Promise<void>;
  compare: () => Promise<void>;
  reset: () => void;
};

export const useNetworkDesignerStore = create<NetworkDesignerStore>((set, get) => ({
  problem: NETWORK_SAMPLES[0].problem,
  solution: null,
  comparison: null,
  solveStatus: "idle",
  compareStatus: "idle",
  error: null,
  setProblem: (problem) => set({ problem, solution: null, comparison: null, error: null }),
  solve: async (algorithm) => {
    set({ solveStatus: "loading", error: null });
    try {
      const res = await solveNetwork(get().problem, algorithm);
      set({ solution: res.solution, solveStatus: "success" });
    } catch (err) {
      set({ solveStatus: "error", error: _message(err, "MST の計算に失敗しました") });
    }
  },
  compare: async () => {
    set({ compareStatus: "loading", error: null });
    try {
      const res = await compareNetwork(get().problem);
      set({ comparison: res, compareStatus: "success" });
    } catch (err) {
      set({ compareStatus: "error", error: _message(err, "比較に失敗しました") });
    }
  },
  reset: () =>
    set({
      problem: NETWORK_SAMPLES[0].problem,
      solution: null,
      comparison: null,
      solveStatus: "idle",
      compareStatus: "idle",
      error: null,
    }),
}));

function _message(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}
