// DeciTima samples │ Phase 7
"use client";

import { Paragraph, Text, XStack, YStack } from "tamagui";
import { GraphCanvas } from "@/components/ui/charts/GraphCanvas";
import type { CandidateSolution, TravelData } from "@/lib/api/types";

/**
 * 旅行プランの可視化。候補の移動区間(leg)を破線、実際に回った閉路(visit_order → 出発地）を
 * 実線・強調で描く。選ばれなかった訪問地はグレー表示。
 */
export function TravelPlanCanvas({
  data,
  solution,
}: {
  data: TravelData;
  solution: CandidateSolution;
}) {
  const plan =
    solution.assignments.problem_type === "travel_planning" ? solution.assignments : null;

  const nodes = data.places.map((p) => ({ id: p.id, label: p.name ?? p.id }));
  const edges = data.legs.map((l) => ({
    id: l.id,
    source: l.endpoints[0],
    target: l.endpoints[1],
    weight: l.travel_cost,
  }));

  // visit_order を閉路にして、連続ペアを結ぶ leg id を強調する
  const legByPair = new Map<string, string>();
  for (const l of data.legs) {
    legByPair.set(_key(l.endpoints[0], l.endpoints[1]), l.id);
  }
  const tour = plan?.visit_order ?? [];
  const tourLegIds: string[] = [];
  for (let i = 0; i < tour.length; i++) {
    const a = tour[i];
    const b = tour[(i + 1) % tour.length];
    const legId = legByPair.get(_key(a, b));
    if (legId) tourLegIds.push(legId);
  }
  const highlighted = new Set(tourLegIds);

  return (
    <YStack gap="$2">
      <Text fontWeight="700">
        旅行プラン({solution.produced_by.name} / {solution.produced_by.implementation})
      </Text>
      {solution.status === "infeasible" || !plan ? (
        <Paragraph color="$red10">
          プランを作れません ── {solution.violations[0]?.message ?? "訪問候補を繋げません"}
        </Paragraph>
      ) : (
        <>
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            highlightNodeIds={plan.selected_place_ids}
            highlightEdgeIds={tourLegIds}
            dashedEdgeIds={edges.filter((e) => !highlighted.has(e.id)).map((e) => e.id)}
          />
          <Paragraph fontSize="$2" color="$color11">
            訪問順: {plan.visit_order.join(" → ")} → {plan.visit_order[0] ?? ""}
          </Paragraph>
          <XStack gap="$4" flexWrap="wrap">
            <Text fontSize="$2">効用 {plan.total_value}</Text>
            <Text fontSize="$2" color={solution.status === "invalid" ? "$red10" : "$color11"}>
              費用 {plan.total_cost} / 予算 {data.budget}
            </Text>
            <Text fontSize="$2" color={solution.status === "invalid" ? "$red10" : "$color11"}>
              時間 {plan.total_time} / 上限 {data.time_budget}
            </Text>
          </XStack>
          {solution.status === "invalid" ? (
            <Paragraph fontSize="$2" color="$red10">
              このプランは予算 or 時間を超えています(DP は移動費用を無視するため起こる)。
            </Paragraph>
          ) : null}
        </>
      )}
    </YStack>
  );
}

function _key(a: string, b: string): string {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}
