// DeciTima samples │ Phase 10
"use client";

import { Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { ProblemJsonEditor } from "@/features/optimization/components/ProblemJsonEditor";
import { SAMPLE_ROUTE_PROBLEM } from "@/features/optimization/sample-problems";
import type { CandidateSolution, SimulationResult } from "@/lib/api/types";
import { useSimulation } from "../hooks/useSimulation";
import { ScenarioComparisonTable } from "./ScenarioComparisonTable";
import { ScenariosJsonEditor } from "./ScenariosJsonEditor";

/** job.result が simulate の結果(base/scenarios を持つ)かどうかの型ガード。 */
function isSimulationResult(
  result: CandidateSolution | SimulationResult,
): result is SimulationResult {
  return "base" in result && "scenarios" in result;
}

/**
 * Simulation 画面の中核。base problem + シナリオ群を編集 → 投入 → 既存ジョブポーリングで
 * 結果を待ち、比較表を出す。README §13「What-if Simulation」の入力面。
 */
export function SimulationPanel() {
  const sim = useSimulation();
  const result = sim.job?.result && isSimulationResult(sim.job.result) ? sim.job.result : null;
  const metricKeys = Object.keys(result?.base.metrics ?? {});

  return (
    <YStack gap="$4" padding="$4" maxWidth={960}>
      <YStack gap="$1">
        <Text fontSize="$6" fontWeight="700">
          What-if Simulation
        </Text>
        <Paragraph color="$color11">
          base problem の一部の値を変えた複数シナリオを解いて比較します。条件を変えると
          結果がどう変わるか(README「どの条件なら、どの選択をするべきか」)を見るための画面。
        </Paragraph>
      </YStack>

      <ProblemJsonEditor
        value={sim.problem}
        samples={[{ label: "route sample", problem: SAMPLE_ROUTE_PROBLEM }]}
        onChange={sim.setProblem}
      />
      <ScenariosJsonEditor value={sim.scenarios} onChange={sim.setScenarios} />

      <XStack gap="$2">
        <StyledButton
          theme="blue"
          disabled={sim.submitStatus === "loading" || sim.job?.status === "running"}
          onPress={() => void sim.submit()}
        >
          {sim.submitStatus === "loading" ? <Spinner /> : "シナリオを実行する"}
        </StyledButton>
      </XStack>

      {sim.error ? <Text color="$red10">{sim.error}</Text> : null}
      {sim.pollError ? <Text color="$red10">{sim.pollError}</Text> : null}

      {sim.job && sim.job.status !== "succeeded" ? (
        <Paragraph color="$color11">状態: {sim.job.status}</Paragraph>
      ) : null}

      {result ? <ScenarioComparisonTable result={result} metricKeys={metricKeys} /> : null}
    </YStack>
  );
}
