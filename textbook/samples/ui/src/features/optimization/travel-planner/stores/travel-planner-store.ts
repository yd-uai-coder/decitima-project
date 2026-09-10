// DeciTima samples │ Phase 7
import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import type {
  AsyncStatus,
  BenchmarkResponse,
  CandidateSolution,
  OptimizationProblem,
} from "@/lib/api/types";
import { compareTravel, solveTravel } from "../api/travel-planner";
import { TRAVEL_SAMPLES } from "../sample-problems";

type TravelPlannerStore = {
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

export const useTravelPlannerStore = create<TravelPlannerStore>((set, get) => ({
  problem: TRAVEL_SAMPLES[0].problem,
  solution: null,
  comparison: null,
  solveStatus: "idle",
  compareStatus: "idle",
  error: null,
  setProblem: (problem) => set({ problem, solution: null, comparison: null, error: null }),
  solve: async (algorithm) => {
    set({ solveStatus: "loading", error: null });
    try {
      const res = await solveTravel(get().problem, algorithm);
      set({ solution: res.solution, solveStatus: "success" });
    } catch (err) {
      set({ solveStatus: "error", error: _message(err, "旅行プランの計算に失敗しました") });
    }
  },
  compare: async () => {
    set({ compareStatus: "loading", error: null });
    try {
      const res = await compareTravel(get().problem);
      set({ comparison: res, compareStatus: "success" });
    } catch (err) {
      set({ compareStatus: "error", error: _message(err, "比較に失敗しました") });
    }
  },
  reset: () =>
    set({
      problem: TRAVEL_SAMPLES[0].problem,
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
