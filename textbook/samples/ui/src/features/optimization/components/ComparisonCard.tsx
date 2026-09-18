// DeciTima samples │ 初出 Phase 14
"use client";

import { Button, Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import type { ComparisonMetrics, OptimizationProblem } from "@/lib/api/types";
import { useComparison } from "../hooks/useComparison";

/**
 * 「LLM と比較してもらう」opt-in カード。README §14「LLM vs Algorithm Comparison」──
 * 同一問題を Algorithm 経路(1回、決定論的)と LLM Only 経路(複数回再実行)の両方で解き、
 * 制約遵守率・最適性・再現性・実行時間・エラー率・検証可能性を並べる。
 * `AlgorithmRecommendationCard`/`ExplanationCard` と同じ「problem_type に依存しない
 * 共通コンポーネント」で、6 Planner Panel から同じ形で呼ばれる。
 */
export function ComparisonCard({ problem }: { problem: OptimizationProblem }) {
  const { result, status, error, run } = useComparison();

  return (
    <YStack gap="$3" padding="$3" borderWidth={1} borderColor="$borderColor" borderRadius="$4">
      <XStack justifyContent="space-between" alignItems="center">
        <Text fontSize="$5" fontWeight="700">
          LLM vs Algorithm 比較
        </Text>
        <Button
          size="$3"
          disabled={status === "loading"}
          onPress={() => void run(problem, { llmRuns: 5 })}
        >
          {status === "loading" ? <Spinner size="small" /> : "LLM と比較する"}
        </Button>
      </XStack>

      {status === "error" ? <Text color="$red10">{error}</Text> : null}

      {result ? (
        <YStack gap="$3">
          <Text fontSize="$2" color="$color11">
            Algorithm: {result.algorithm_used.name}({result.algorithm_used.implementation}) /
            LLM Only: {result.llm_results.length}回試行
          </Text>
          <MetricsTable metrics={result.metrics} />
          {result.narrative ? (
            <YStack gap="$2">
              <Paragraph fontSize="$2">{result.narrative.summary}</Paragraph>
              <NarrativeSection label="制約遵守率" text={result.narrative.constraint_compliance_note} />
              <NarrativeSection label="最適性" text={result.narrative.optimality_note} />
              <NarrativeSection label="再現性" text={result.narrative.reproducibility_note} />
              <NarrativeSection label="検証可能性" text={result.narrative.verifiability_note} />
            </YStack>
          ) : null}
        </YStack>
      ) : null}
    </YStack>
  );
}

function MetricsTable({ metrics }: { metrics: ComparisonMetrics }) {
  const rows: [string, string][] = [
    [
      "制約遵守率",
      `Algorithm ${formatPercent(metrics.constraint_compliance_rate_algorithm)} / ` +
        `LLM ${formatPercent(metrics.constraint_compliance_rate_llm)}`,
    ],
    [
      "最適性(1.0=Algorithmと同等)",
      metrics.optimality_avg_quality_ratio_llm != null
        ? metrics.optimality_avg_quality_ratio_llm.toFixed(2)
        : "比較不能",
    ],
    ["再現性(LLMが出した構造の種類数)", String(metrics.reproducibility_distinct_solutions_llm)],
    [
      "実行時間(中央値)",
      `Algorithm ${metrics.execution_time_ms_algorithm.toFixed(1)}ms / ` +
        `LLM ${metrics.execution_time_ms_llm_median.toFixed(1)}ms`,
    ],
    ["エラー率(LLM)", formatPercent(metrics.error_rate_llm)],
  ];
  return (
    <YStack gap="$1" padding="$2" borderWidth={1} borderColor="$borderColor" borderRadius="$3">
      {rows.map(([label, value]) => (
        <XStack key={label} justifyContent="space-between">
          <Text fontSize="$2" color="$color11">
            {label}
          </Text>
          <Text fontSize="$2" fontWeight="700">
            {value}
          </Text>
        </XStack>
      ))}
    </YStack>
  );
}

function NarrativeSection({ label, text }: { label: string; text: string }) {
  return (
    <YStack gap="$1">
      <Text fontSize="$2" fontWeight="700">
        {label}
      </Text>
      <Paragraph fontSize="$2">{text}</Paragraph>
    </YStack>
  );
}

function formatPercent(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}
