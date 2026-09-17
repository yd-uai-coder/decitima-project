// DeciTima samples │ Phase 11(11-8)
"use client";

import { Paragraph, Text, YStack } from "tamagui";
import { NaturalLanguageInputForm } from "./NaturalLanguageInputForm";
import { StructuredProblemCard } from "./StructuredProblemCard";

/**
 * Structuring 画面の中核。README §11「Human-in-the-loop」を実演する:
 * 自然言語入力 → AIが理解した条件の確認 → 修正 → 該当ドメインページで最適化。
 */
export function StructuringPanel() {
  return (
    <YStack gap="$4" padding="$4" maxWidth={960}>
      <YStack gap="$1">
        <Text fontSize="$6" fontWeight="700">
          自然言語で問題を作る
        </Text>
        <Paragraph color="$color11">
          要求を自然言語で入力すると、LLM が objectives・constraints・条件を抽出して問題を
          構造化します。LLM の出力は必ず Validation を通し、確認してから最適化に進みます
          (README「LLM に最適解を計算させない」── LLM は理解・構造化・説明だけを担当します)。
        </Paragraph>
      </YStack>

      <NaturalLanguageInputForm />
      <StructuredProblemCard />
    </YStack>
  );
}
