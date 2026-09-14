// DeciTima samples │ Phase 10
import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import type { AsyncStatus, OptimizationProblem, ScenarioOverride } from "@/lib/api/types";
import { SAMPLE_ROUTE_PROBLEM } from "../../sample-problems";
import { submitSimulation } from "../api/simulate";

type SimulationStore = {
  problem: OptimizationProblem;
  scenarios: ScenarioOverride[];
  jobId: string | null; // 投入後、結果は `useJobPolling(jobId)`(Phase 9-9)がポーリングする
  submitStatus: AsyncStatus;
  error: string | null;
  setProblem: (problem: OptimizationProblem) => void;
  setScenarios: (scenarios: ScenarioOverride[]) => void;
  submit: () => Promise<void>;
  reset: () => void;
};

const INITIAL_SCENARIOS: ScenarioOverride[] = [{ label: "as-is", overrides: {} }];

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  problem: SAMPLE_ROUTE_PROBLEM,
  scenarios: INITIAL_SCENARIOS,
  jobId: null,
  submitStatus: "idle",
  error: null,
  setProblem: (problem) => set({ problem, jobId: null, error: null }),
  setScenarios: (scenarios) => set({ scenarios, jobId: null, error: null }),
  submit: async () => {
    set({ submitStatus: "loading", error: null, jobId: null });
    try {
      const res = await submitSimulation({ problem: get().problem, scenarios: get().scenarios });
      set({ jobId: res.job_id, submitStatus: "success" });
    } catch (err) {
      set({
        submitStatus: "error",
        error: err instanceof ApiError ? err.message : "シナリオの投入に失敗しました",
      });
    }
  },
  reset: () =>
    set({
      problem: SAMPLE_ROUTE_PROBLEM,
      scenarios: INITIAL_SCENARIOS,
      jobId: null,
      submitStatus: "idle",
      error: null,
    }),
}));
