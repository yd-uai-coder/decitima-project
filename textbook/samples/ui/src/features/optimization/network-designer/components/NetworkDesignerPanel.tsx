// DeciTima samples │ Phase 5
"use client";

import { Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { BenchmarkTable } from "@/features/optimization/components/BenchmarkTable";
import { ProblemJsonEditor } from "@/features/optimization/components/ProblemJsonEditor";
import { MstResultCanvas } from "@/features/optimization/network-designer/components/MstResultCanvas";
import { useNetworkDesigner } from "@/features/optimization/network-designer/hooks/useNetworkDesigner";
import { NETWORK_SAMPLES } from "@/features/optimization/network-designer/sample-problems";

/**
 * Network Designer 画面の中核。拠点と敷設可能リンクを編集 → 「設計する」で MST を可視化、
 * 「比較」で Kruskal / Prim / networkx を横並び実測する。
 */
export function NetworkDesignerPanel() {
  const nd = useNetworkDesigner();
  const data = nd.problem.problem_type === "network_design" ? nd.problem.data : null;

  return (
    <YStack gap="$4" padding="$4" maxWidth={960}>
      <YStack gap="$1">
        <Text fontSize="$6" fontWeight="700">
          Network Designer
        </Text>
        <Paragraph color="$color11">
          すべての拠点を最小コストで繋ぐネットワーク(最小全域木)。Kruskal は「辺を軽い順に、
          閉路にならないものだけ」、Prim は「木の外へ出る最小の辺」を選びます。
        </Paragraph>
      </YStack>

      <ProblemJsonEditor value={nd.problem} samples={NETWORK_SAMPLES} onChange={nd.setProblem} />

      <XStack gap="$2">
        <StyledButton
          theme="blue"
          disabled={nd.solveStatus === "loading"}
          onPress={() => void nd.solve()}
        >
          {nd.solveStatus === "loading" ? <Spinner /> : "設計する(Kruskal)"}
        </StyledButton>
        <StyledButton disabled={nd.compareStatus === "loading"} onPress={() => void nd.compare()}>
          {nd.compareStatus === "loading" ? <Spinner /> : "Kruskal / Prim / networkx 比較"}
        </StyledButton>
      </XStack>

      {nd.error ? <Text color="$red10">{nd.error}</Text> : null}

      {data && nd.solution ? <MstResultCanvas data={data} solution={nd.solution} /> : null}

      {nd.comparison ? <BenchmarkTable entries={nd.comparison.entries} /> : null}
    </YStack>
  );
}
