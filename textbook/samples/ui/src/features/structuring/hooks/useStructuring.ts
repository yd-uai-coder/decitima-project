// DeciTima samples │ Phase 11(11-8)
"use client";

import { useStructuringStore } from "../stores/structuring-store";

/** structuring-store の薄いラッパ(個別セレクタで購読。他ドメインの use*Planner と同型)。 */
export function useStructuring() {
  const text = useStructuringStore((s) => s.text);
  const problem = useStructuringStore((s) => s.problem);
  const notes = useStructuringStore((s) => s.notes);
  const status = useStructuringStore((s) => s.status);
  const error = useStructuringStore((s) => s.error);
  const setText = useStructuringStore((s) => s.setText);
  const setProblem = useStructuringStore((s) => s.setProblem);
  const submit = useStructuringStore((s) => s.submit);
  const reset = useStructuringStore((s) => s.reset);
  return { text, problem, notes, status, error, setText, setProblem, submit, reset };
}
