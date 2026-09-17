// DeciTima samples │ 初出 Phase 12
"use client";

import { Button, Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import type { OptimizationProblem } from "@/lib/api/types";
import { useAlgorithmRecommendation } from "../hooks/useAlgorithmRecommendation";

/**
 * 「アルゴリズムを推薦してもらう」opt-in カード。solve の既定選択には一切影響しない
 * (README「LLM単独では最終決定しない」)── ここで確認した名前を、solve 実行時に
 * `?algorithm=` へ手動で渡すかどうかは呼び出し側(各 planner panel)の判断に委ねる。
 * problem_type に依存しない共通コンポーネント(6ドメイン全パネルから同じ形で呼ばれる、
 * `useJobPolling`/`usePendingProblemHydration` と同じ置き場所の考え方)。
 */
export function AlgorithmRecommendationCard({ problem }: { problem: OptimizationProblem }) {
  const { result, status, error, run } = useAlgorithmRecommendation();

  return (
    <YStack gap="$3" padding="$3" borderWidth={1} borderColor="$borderColor" borderRadius="$4">
      <XStack justifyContent="space-between" alignItems="center">
        <Text fontSize="$5" fontWeight="700">
          アルゴリズムの推薦
        </Text>
        <Button size="$3" disabled={status === "loading"} onPress={() => void run(problem)}>
          {status === "loading" ? <Spinner size="small" /> : "推薦してもらう"}
        </Button>
      </XStack>

      {status === "error" ? <Text color="$red10">{error}</Text> : null}

      {result ? (
        <YStack gap="$2">
          {result.notes.map((note) => (
            <Paragraph key={note} color="$color11" fontSize="$2">
              {note}
            </Paragraph>
          ))}
          {result.recommendations.map((rec) => (
            <YStack
              key={rec.name}
              gap="$1"
              padding="$2"
              borderWidth={1}
              borderColor={rec.is_rule_preferred ? "$blue8" : "$borderColor"}
              borderRadius="$3"
            >
              <XStack gap="$2" alignItems="center">
                <Text fontWeight="700">{rec.name}</Text>
                <Text fontSize="$1" color="$color11">
                  {rec.implementation}
                </Text>
                {rec.is_rule_preferred ? (
                  <Text fontSize="$1" color="$blue10">
                    ルールベースの既定
                  </Text>
                ) : null}
                {rec.llm_rank != null ? (
                  <Text fontSize="$1" color="$green10">
                    LLM推薦 {rec.llm_rank}位
                  </Text>
                ) : null}
              </XStack>
              <Text fontSize="$2" color="$color11">
                {rec.description}
              </Text>
              {rec.llm_comment ? <Text fontSize="$2">{rec.llm_comment}</Text> : null}
              {rec.time_complexity ? (
                <Text fontSize="$1" color="$color10">
                  計算量: {rec.time_complexity}
                </Text>
              ) : null}
            </YStack>
          ))}
        </YStack>
      ) : null}
    </YStack>
  );
}
