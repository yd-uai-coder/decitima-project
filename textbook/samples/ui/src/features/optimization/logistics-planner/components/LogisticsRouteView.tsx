// DeciTima samples │ Phase 9
"use client";

import { Paragraph, Text, XStack, YStack } from "tamagui";
import { GraphCanvas } from "@/components/ui/charts/GraphCanvas";
import type { CandidateSolution, LogisticsData } from "@/lib/api/types";

/**
 * 配送計画の可視化。車両ごとに GraphCanvas を1枚ずつ並べ(small multiples)、その車両が
 * 訪れる配送先ノード(+ デポ)だけをハイライトする。
 *
 * 区間(道路)の色分けはしない ── API は「デポ→各配送先の訪問順」までしか返さず、
 * 2 地点間で実際にどの道路区間を通ったか(Floyd-Warshall が内部で選んだ最短経路の内訳)は
 * 返さないため、正確な経路線を引けるのはノードまで(Phase 9 のスコープ外)。
 */
export function LogisticsRouteView({
  data,
  solution,
}: {
  data: LogisticsData;
  solution: CandidateSolution;
}) {
  const plan =
    solution.assignments.problem_type === "logistics_planning" ? solution.assignments : null;

  if (solution.status === "infeasible" || !plan) {
    return (
      <Paragraph color="$red10">
        配送計画を組めません ──{" "}
        {solution.violations[0]?.message ?? "容量・到達可能性を確認してください"}
      </Paragraph>
    );
  }

  const nodes = data.nodes.map((n) => ({ id: n.id, label: n.label ?? n.id, x: n.x, y: n.y }));
  const edges = data.segments.map((s) => ({
    id: s.id,
    source: s.source,
    target: s.target,
    directed: s.directed,
  }));
  const nodeIdByDelivery = new Map(data.deliveries.map((d) => [d.id, d.node_id]));

  return (
    <YStack gap="$3">
      <Text fontWeight="700">
        配送計画({solution.produced_by.name} / {solution.produced_by.implementation})
      </Text>
      <XStack gap="$4" flexWrap="wrap">
        <Text fontSize="$2">総距離 {plan.total_distance}</Text>
        <Text fontSize="$2">使用台数 {solution.metrics.vehicles_used ?? plan.routes.length}</Text>
      </XStack>

      <XStack gap="$3" flexWrap="wrap">
        {plan.routes.map((route) => {
          const visitedNodeIds = [
            data.depot_id,
            ...route.stop_ids.map((sid) => nodeIdByDelivery.get(sid) ?? sid),
          ];
          return (
            <YStack key={route.vehicle_id} gap="$1">
              <Text fontSize="$3" fontWeight="600">
                車両 {route.vehicle_id} ── 距離 {route.distance}
              </Text>
              <GraphCanvas
                nodes={nodes}
                edges={edges}
                highlightNodeIds={visitedNodeIds}
                width={300}
                height={220}
              />
              <Paragraph fontSize="$2" color="$color11">
                訪問順: {route.stop_ids.length > 0 ? route.stop_ids.join(" → ") : "(配送先なし)"}
              </Paragraph>
            </YStack>
          );
        })}
      </XStack>

      {solution.status === "invalid" ? (
        <Paragraph fontSize="$2" color="$red10">
          {solution.violations[0]?.message ?? "制約に違反しています"}
        </Paragraph>
      ) : null}
    </YStack>
  );
}
