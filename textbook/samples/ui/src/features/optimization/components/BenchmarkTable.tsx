// DeciTima samples │ Phase 3
"use client";

import { Text, XStack, YStack } from "tamagui";
import type { BenchmarkEntry } from "@/lib/api/types";

const COLUMNS: { key: string; label: string; get: (e: BenchmarkEntry) => string }[] = [
  { key: "algo", label: "アルゴリズム", get: (e) => e.algorithm.name },
  { key: "impl", label: "実装", get: (e) => e.algorithm.implementation },
  { key: "status", label: "状態", get: (e) => e.solution_status },
  { key: "time", label: "実行時間(中央値 ms)", get: (e) => e.elapsed_ms_median.toFixed(3) },
  { key: "ops", label: "操作回数", get: (e) => (e.operation_count ?? "―").toString() },
  { key: "mem", label: "ピークメモリ(KB)", get: (e) => e.peak_memory_kb.toFixed(1) },
  { key: "quality", label: "品質比", get: (e) => (e.quality_ratio == null ? "―" : e.quality_ratio.toFixed(3)) },
  { key: "viol", label: "違反(hard/soft)", get: (e) => `${e.hard_violations}/${e.soft_violations}` },
];

/**
 * Algorithm × 6 指標の比較テーブル。README §14 の出力形そのもの。
 * 操作回数はアルゴリズム定義の単位なので列見出しでは強調しない(注記は Panel 側)。
 */
export function BenchmarkTable({ entries }: { entries: BenchmarkEntry[] }) {
  return (
    <YStack borderWidth={1} borderColor="$borderColor" borderRadius="$4" overflow="hidden">
      <XStack backgroundColor="$color3">
        {COLUMNS.map((c) => (
          <Text key={c.key} flex={1} padding="$2" fontSize="$1" fontWeight="700">
            {c.label}
          </Text>
        ))}
      </XStack>
      {entries.map((e) => (
        <XStack key={e.algorithm.name} borderTopWidth={1} borderColor="$borderColor">
          {COLUMNS.map((c) => (
            <Text key={c.key} flex={1} padding="$2" fontSize="$2">
              {c.get(e)}
            </Text>
          ))}
        </XStack>
      ))}
    </YStack>
  );
}
