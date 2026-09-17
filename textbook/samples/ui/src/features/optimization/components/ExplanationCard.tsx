// DeciTima samples │ 初出 Phase 13
"use client";

import { Button, Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import type { OptimizationProblem } from "@/lib/api/types";
import { useSolutionExplanation } from "../hooks/useSolutionExplanation";

/**
 * 「この解を説明してもらう」opt-in カード。README §13 の説明対象5項目(なぜこの解か /
 * どの制約が重要だったか / どのアルゴリズムを使ったか / 他の候補との違い / 改善余地)を表示する。
 * `AlgorithmRecommendationCard` と同じ「problem_type に依存しない共通コンポーネント」だが、
 * 説明は永続化済みの solution_id を要求するため、押下時に現在の問題を solve(persist: true)
 * し直してから explain を呼ぶ2段階になる点が recommend と異なる(`explanation-store.ts` 参照)。
 */
export function ExplanationCard({
  problem,
  algorithm,
}: {
  problem: OptimizationProblem;
  algorithm?: string;
}) {
  const { result, status, error, run } = useSolutionExplanation();

  return (
    <YStack gap="$3" padding="$3" borderWidth={1} borderColor="$borderColor" borderRadius="$4">
      <XStack justifyContent="space-between" alignItems="center">
        <Text fontSize="$5" fontWeight="700">
          解の説明
        </Text>
        <Button
          size="$3"
          disabled={status === "loading"}
          onPress={() => void run(problem, { algorithm })}
        >
          {status === "loading" ? <Spinner size="small" /> : "この解を説明してもらう"}
        </Button>
      </XStack>

      {status === "error" ? <Text color="$red10">{error}</Text> : null}

      {result ? (
        <YStack gap="$3">
          <Text fontSize="$2" color="$color11">
            {result.algorithm_name} で計算された解(solution_id: {result.solution_id})
          </Text>
          {result.notes.map((note) => (
            <Paragraph key={note} color="$color11" fontSize="$2">
              {note}
            </Paragraph>
          ))}
          <ExplanationSection label="なぜこの解になったか" text={result.why_this_solution} />
          <ExplanationSection label="どの制約が重要だったか" text={result.key_constraints} />
          <ExplanationSection label="どのアルゴリズムを使ったか" text={result.algorithm_rationale} />
          <ExplanationSection label="他の候補との違い" text={result.alternatives_comparison} />
          <ExplanationSection label="改善余地" text={result.improvement_notes} />
        </YStack>
      ) : null}
    </YStack>
  );
}

function ExplanationSection({ label, text }: { label: string; text: string }) {
  return (
    <YStack gap="$1">
      <Text fontSize="$2" fontWeight="700">
        {label}
      </Text>
      <Paragraph fontSize="$2">{text}</Paragraph>
    </YStack>
  );
}
