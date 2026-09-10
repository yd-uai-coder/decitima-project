// DeciTima samples │ Phase 7
"use client";

import { Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { BenchmarkTable } from "@/features/optimization/components/BenchmarkTable";
import { ProblemJsonEditor } from "@/features/optimization/components/ProblemJsonEditor";
import { TravelPlanCanvas } from "@/features/optimization/travel-planner/components/TravelPlanCanvas";
import { useTravelPlanner } from "@/features/optimization/travel-planner/hooks/useTravelPlanner";
import { TRAVEL_SAMPLES } from "@/features/optimization/travel-planner/sample-problems";

/**
 * Travel Planner 画面の中核。訪問候補・予算・時間・好みを編集 → 「プランを作る」で
 * Knapsack DP の結果を可視化、「比較」で DP / Greedy / BruteForce を横並び実測する。
 */
export function TravelPlannerPanel() {
  const tp = useTravelPlanner();
  const data = tp.problem.problem_type === "travel_planning" ? tp.problem.data : null;

  return (
    <YStack gap="$4" padding="$4" maxWidth={960}>
      <YStack gap="$1">
        <Text fontSize="$6" fontWeight="700">
          Travel Planner
        </Text>
        <Paragraph color="$color11">
          予算・時間・好みから訪問地を選び、回る順を決めます。Knapsack DP は「移動費用を無視した
          選択」= 上界。実際に巡回して戻る移動分を足すと予算を超えることがあり、その場合は invalid
          になります。Greedy は 1 つ選ぶたびに実際の巡回コストで判定します。
        </Paragraph>
      </YStack>

      <ProblemJsonEditor value={tp.problem} samples={TRAVEL_SAMPLES} onChange={tp.setProblem} />

      <XStack gap="$2">
        <StyledButton
          theme="blue"
          disabled={tp.solveStatus === "loading"}
          onPress={() => void tp.solve()}
        >
          {tp.solveStatus === "loading" ? <Spinner /> : "プランを作る(Knapsack DP)"}
        </StyledButton>
        <StyledButton disabled={tp.compareStatus === "loading"} onPress={() => void tp.compare()}>
          {tp.compareStatus === "loading" ? <Spinner /> : "DP / Greedy / BruteForce 比較"}
        </StyledButton>
      </XStack>

      {tp.error ? <Text color="$red10">{tp.error}</Text> : null}

      {data && tp.solution ? <TravelPlanCanvas data={data} solution={tp.solution} /> : null}

      {tp.comparison ? <BenchmarkTable entries={tp.comparison.entries} /> : null}
    </YStack>
  );
}
