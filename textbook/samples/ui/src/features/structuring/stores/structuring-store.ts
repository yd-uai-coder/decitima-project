// DeciTima samples │ Phase 11(11-8)
import { create } from "zustand";
import { ApiError } from "@/lib/api/client";
import type { AsyncStatus, OptimizationProblem } from "@/lib/api/types";
import { submitStructuring } from "../api/structure";

type StructuringStore = {
  text: string;
  conversationId: string | null;
  problem: OptimizationProblem | null;
  notes: string[];
  status: AsyncStatus;
  error: string | null;
  setText: (text: string) => void;
  setProblem: (problem: OptimizationProblem) => void; // 確認カードでの手直し用(README「修正する」)
  submit: () => Promise<void>;
  reset: () => void;
};

/**
 * Structuring 画面(README §11)が要る状態。`submit()` で `POST /api/v1/structure` を叩き、
 * 返ってきた `problem`/`notes` を確認カードに渡す。`setProblem` は確認カード上での手直し
 * (既存共有 `ProblemJsonEditor` を再利用)を local state に反映するだけで、再度 LLM は呼ばない。
 */
export const useStructuringStore = create<StructuringStore>((set, get) => ({
  text: "",
  conversationId: null,
  problem: null,
  notes: [],
  status: "idle",
  error: null,
  setText: (text) => set({ text }),
  setProblem: (problem) => set({ problem }),
  submit: async () => {
    set({ status: "loading", error: null });
    try {
      const res = await submitStructuring({
        text: get().text,
        conversation_id: get().conversationId,
      });
      set({
        conversationId: res.conversation_id,
        problem: res.problem,
        notes: res.notes,
        status: "success",
      });
    } catch (err) {
      set({
        status: "error",
        error: err instanceof ApiError ? err.message : "構造化に失敗しました",
      });
    }
  },
  reset: () =>
    set({
      text: "",
      conversationId: null,
      problem: null,
      notes: [],
      status: "idle",
      error: null,
    }),
}));
