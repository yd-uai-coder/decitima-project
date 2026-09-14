// DeciTima samples │ Phase 10
"use client";

import { Paragraph, Text, XStack, YStack } from "tamagui";
import type { SimulationResult } from "@/lib/api/types";

const STATUS_COLOR: Record<string, string> = {
  valid: "$color12",
  invalid: "$yellow10",
  infeasible: "$red10",
  invalid_scenario: "$red10",
};

/**
 * base + シナリオ群を横並べにした比較表(README §13 の「車両数・配送時間・コスト」表と
 * 同じ発想)。metricKeys は表示したい metrics のキー(ドメインごとに違うので呼び出し側が
 * 選ぶ ── 汎用 override の設計と同じく、ドメイン知識は UI 側に閉じる)。
 */
export function ScenarioComparisonTable({
  result,
  metricKeys,
}: {
  result: SimulationResult;
  metricKeys: string[];
}) {
  const rows = [{ ...result.base, label: "base(as-is)" }, ...result.scenarios];

  return (
    <YStack gap="$2">
      <XStack gap="$3">
        <Text fontWeight="700" width={140}>
          シナリオ
        </Text>
        <Text fontWeight="700" width={100}>
          状態
        </Text>
        {metricKeys.map((key) => (
          <Text key={key} fontWeight="700" width={100}>
            {key}
          </Text>
        ))}
      </XStack>
      {rows.map((row, i) => (
        <XStack key={`${row.label}-${i}`} gap="$3">
          <Text width={140}>{row.label}</Text>
          <Text width={100} color={STATUS_COLOR[row.status] ?? "$color12"}>
            {row.status}
          </Text>
          {metricKeys.map((key) => (
            <Text key={key} width={100}>
              {row.metrics[key] ?? "—"}
            </Text>
          ))}
        </XStack>
      ))}
      {result.sensitivity && (
        <Paragraph fontSize="$2" color="$color11">
          感度分析: 閾値={result.sensitivity.threshold_value ?? "見つからず"}(評価点
          {Object.keys(result.sensitivity.evaluated).length}件)
        </Paragraph>
      )}
    </YStack>
  );
}
