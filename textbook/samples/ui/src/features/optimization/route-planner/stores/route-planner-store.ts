// DeciTima samples │ Phase 4
import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import type {
  AsyncStatus,
  BenchmarkResponse,
  CandidateSolution,
  OptimizationProblem,
} from "@/lib/api/types";
import { compareRoute, solveRoute } from "../api/route-planner";
import { ROUTE_SAMPLES } from "../sample-problems";

type RoutePlannerStore = {
  problem: OptimizationProblem;
  solution: CandidateSolution | null;
  comparison: BenchmarkResponse | null;
  solveStatus: AsyncStatus;
  compareStatus: AsyncStatus;
  error: string | null;
  setProblem: (problem: OptimizationProblem) => void;
  // solve: 1 アルゴリズムで解いて経路を得る(可視化用)。algorithm 省略で rule-based。
  solve: (algorithm?: string) => Promise<void>;
  // compare: registry の全 route アルゴリズムを実測して並べる。
  compare: () => Promise<void>;
  reset: () => void;
};

export const useRoutePlannerStore = create<RoutePlannerStore>((set, get) => ({
  problem: ROUTE_SAMPLES[0].problem,
  solution: null,
  comparison: null,
  solveStatus: "idle",
  compareStatus: "idle",
  error: null,
  setProblem: (problem) => set({ problem, solution: null, comparison: null, error: null }),
  solve: async (algorithm) => {
    set({ solveStatus: "loading", error: null });
    try {
      const res = await solveRoute(get().problem, algorithm);
      set({ solution: res.solution, solveStatus: "success" });
    } catch (err) {
      set({ solveStatus: "error", error: _message(err, "解の計算に失敗しました") });
    }
  },
  compare: async () => {
    set({ compareStatus: "loading", error: null });
    try {
      const res = await compareRoute(get().problem);
      set({ comparison: res, compareStatus: "success" });
    } catch (err) {
      set({ compareStatus: "error", error: _message(err, "比較に失敗しました") });
    }
  },
  reset: () =>
    set({
      problem: ROUTE_SAMPLES[0].problem,
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
