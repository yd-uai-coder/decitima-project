// DeciTima samples │ Phase 3
"use client";

import { GroupedBarChart } from "@/components/ui/charts/GroupedBarChart";
import type { BenchmarkEntry } from "@/lib/api/types";

/**
 * アルゴリズム別に「実行時間 / 操作回数 / メモリ」を並べたグループ棒。
 * 単位が違う 3 指標を 1 枚に載せるため、各指標を「その指標の最大値 = 1」に正規化する
 * (絶対値はテーブル側で見る)。
 */
export function BenchmarkComparisonChart({ entries }: { entries: BenchmarkEntry[] }) {
  const names = entries.map((e) => e.algorithm.name);
  const time = entries.map((e) => e.elapsed_ms_median);
  const ops = entries.map((e) => e.operation_count ?? 0);
  const mem = entries.map((e) => e.peak_memory_kb);

  const norm = (xs: number[]) => {
    const m = Math.max(...xs, 1);
    return xs.map((x) => x / m);
  };

  return (
    <GroupedBarChart
      groups={names}
      series={[
        { label: "実行時間(相対)", values: norm(time) },
        { label: "操作回数(相対)", values: norm(ops) },
        { label: "メモリ(相対)", values: norm(mem) },
      ]}
      valueFormat={(v) => v.toFixed(2)}
    />
  );
}
