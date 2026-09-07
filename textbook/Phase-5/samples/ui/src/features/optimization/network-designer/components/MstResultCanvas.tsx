"use client";

import { Paragraph, Text, YStack } from "tamagui";
import { GraphCanvas } from "@/components/ui/charts/GraphCanvas";
import type { CandidateSolution, NetworkDesignData } from "@/lib/api/types";

/**
 * MST の可視化。候補リンクを破線で、選ばれたリンク(全域木)を実線・強調色で描く。
 */
export function MstResultCanvas({
  data,
  solution,
}: {
  data: NetworkDesignData;
  solution: CandidateSolution;
}) {
  const mst =
    solution.assignments.problem_type === "network_design" ? solution.assignments : null;

  const edges = data.links.map((l) => ({
    id: l.id,
    source: l.endpoints[0],
    target: l.endpoints[1],
    weight: l.weight,
  }));
  const selected = new Set(mst?.selected_link_ids ?? []);

  return (
    <YStack gap="$2">
      <Text fontWeight="700">
        最小全域木({solution.produced_by.name} / {solution.produced_by.implementation})
      </Text>
      {solution.status === "infeasible" || !mst ? (
        <Paragraph color="$red10">
          全域木を作れません ── {solution.violations[0]?.message ?? "候補リンクでは全拠点が繋がりません"}
        </Paragraph>
      ) : (
        <>
          <GraphCanvas
            nodes={data.nodes}
            edges={edges}
            highlightEdgeIds={mst.selected_link_ids}
            dashedEdgeIds={edges.filter((e) => !selected.has(e.id)).map((e) => e.id)}
          />
          <Paragraph fontSize="$2" color="$color11">
            敷設: {mst.selected_link_ids.join(", ")}(総コスト {mst.total_weight})
          </Paragraph>
        </>
      )}
    </YStack>
  );
}
