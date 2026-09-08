// DeciTima samples │ Phase 3
"use client";

import { MultiLineChart } from "@/components/ui/charts/MultiLineChart";

export type CurvePoint = { size: number; opsByAlgorithm: Record<string, number> };

/**
 * 入力サイズ別カーブ ── x = 問題サイズ、y = 操作回数(対数軸)。
 * 全探索が指数的に伸び、Dijkstra が緩やかなことが 1 枚で見える。
 * データは呼び出し側が「サイズを振って benchmark を N 回叩く」ことで用意する。
 */
export function InputSizeCurveChart({ points }: { points: CurvePoint[] }) {
  const algos = Array.from(new Set(points.flatMap((p) => Object.keys(p.opsByAlgorithm))));
  return (
    <MultiLineChart
      xLabels={points.map((p) => p.size)}
      logScale
      series={algos.map((name) => ({
        label: name,
        points: points.map((p) => p.opsByAlgorithm[name] ?? 0),
      }))}
      valueFormat={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v.toFixed(0))}
    />
  );
}
