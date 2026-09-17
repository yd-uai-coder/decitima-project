// DeciTima samples │ Phase 11(11-8)
import { create } from "zustand";
import type { OptimizationProblem } from "@/lib/api/types";

type PendingProblemStore = {
  pending: OptimizationProblem | null;
  setPending: (problem: OptimizationProblem) => void;
  consumePending: (problemType: OptimizationProblem["problem_type"]) => OptimizationProblem | null;
};

/**
 * features/structuring(README §11 の確認カード)で確定した OptimizationProblem を、
 * 遷移先の各ドメインページへ一時的に受け渡すための共有ストア。1件だけ保持し、
 * `consumePending()` は取り出すと同時に消費する(ページの再マウントや「戻る」操作での
 * 意図しない再適用を防ぐ)。problem_type が一致しないページからの呼び出しは無視する。
 */
export const usePendingProblemStore = create<PendingProblemStore>((set, get) => ({
  pending: null,
  setPending: (problem) => set({ pending: problem }),
  consumePending: (problemType) => {
    const pending = get().pending;
    if (!pending || pending.problem_type !== problemType) return null;
    set({ pending: null });
    return pending;
  },
}));
