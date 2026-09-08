// DeciTima samples │ Phase 3
"use client";

import { useBenchmarkStore } from "../stores/benchmark-store";

/**
 * ベンチマーク store の薄いラッパ。コンポーネントは result / status / run だけ見れば済む。
 */
export function useBenchmark() {
  const result = useBenchmarkStore((s) => s.result);
  const status = useBenchmarkStore((s) => s.status);
  const error = useBenchmarkStore((s) => s.error);
  const run = useBenchmarkStore((s) => s.run);
  const reset = useBenchmarkStore((s) => s.reset);
  return { result, status, error, run, reset };
}
