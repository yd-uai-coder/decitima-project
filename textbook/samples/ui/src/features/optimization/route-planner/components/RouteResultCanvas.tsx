// DeciTima samples │ Phase 4
"use client";

import { Paragraph, Text, YStack } from "tamagui";
import { GraphCanvas } from "@/components/ui/charts/GraphCanvas";
import type { CandidateSolution, RouteData } from "@/lib/api/types";

/**
 * 経路の可視化。GraphCanvas に問題のグラフを描き、解の経路(path_edge_ids / path_node_ids)を
 * 強調色でハイライトする。解が infeasible ならその旨を出す。
 */
export function RouteResultCanvas({
  data,
  solution,
}: {
  data: RouteData;
  solution: CandidateSolution;
}) {
  const path =
    solution.assignments.problem_type === "route_planning" ? solution.assignments : null;

  return (
    <YStack gap="$2">
      <Text fontWeight="700">
        経路({solution.produced_by.name} / {solution.produced_by.implementation})
      </Text>
      {solution.status === "infeasible" || !path ? (
        <Paragraph color="$red10">
          解なし ── {solution.violations[0]?.message ?? "この条件では経路が存在しません"}
        </Paragraph>
      ) : (
        <>
          <GraphCanvas
            nodes={data.nodes}
            edges={data.edges}
            highlightNodeIds={path.path_node_ids}
            highlightEdgeIds={path.path_edge_ids}
          />
          <Paragraph fontSize="$2" color="$color11">
            {path.path_node_ids.join(" → ")}(総距離 {path.total_weight})
          </Paragraph>
        </>
      )}
    </YStack>
  );
}
