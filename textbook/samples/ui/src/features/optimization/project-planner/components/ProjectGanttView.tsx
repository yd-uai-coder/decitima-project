"use client";

import { Paragraph, Text, XStack, YStack } from "tamagui";
import { GanttCanvas } from "@/components/ui/charts/GanttCanvas";
import { GraphCanvas } from "@/components/ui/charts/GraphCanvas";
import type { CandidateSolution, ProjectData } from "@/lib/api/types";

/**
 * スケジュールの可視化。依存 DAG を GraphCanvas で、各タスクの開始〜終了を GanttCanvas で描く。
 * クリティカルパスのタスクは赤で強調。cpm(資源無視)が資源超過で invalid のとき、赤メッセージ。
 */
export function ProjectGanttView({
  data,
  solution,
}: {
  data: ProjectData;
  solution: CandidateSolution;
}) {
  const plan =
    solution.assignments.problem_type === "project_scheduling" ? solution.assignments : null;

  const nameById = new Map(data.tasks.map((t) => [t.id, t.name ?? t.id]));
  const nodes = data.tasks.map((t) => ({ id: t.id, label: t.name ?? t.id }));
  const edges = data.dependencies.map((d) => ({
    id: d.id,
    source: d.predecessor,
    target: d.successor,
    directed: true,
  }));

  if (solution.status === "infeasible" || !plan) {
    return (
      <Paragraph color="$red10">
        スケジュールを組めません ── {solution.violations[0]?.message ?? "依存グラフに閉路があります"}
      </Paragraph>
    );
  }

  const critical = new Set(plan.critical_path);
  const bars = plan.schedule.map((s) => ({
    id: s.task_id,
    label: nameById.get(s.task_id) ?? s.task_id,
    start: s.start,
    end: s.finish,
    slack: s.slack,
    highlight: critical.has(s.task_id),
  }));

  return (
    <YStack gap="$2">
      <Text fontWeight="700">
        スケジュール({solution.produced_by.name} / {solution.produced_by.implementation})
      </Text>

      <GraphCanvas nodes={nodes} edges={edges} highlightNodeIds={plan.critical_path} />
      <GanttCanvas bars={bars} />

      <Paragraph fontSize="$2" color="$color11">
        クリティカルパス: {plan.critical_path.map((id) => nameById.get(id) ?? id).join(" → ")}
      </Paragraph>
      <XStack gap="$4" flexWrap="wrap">
        <Text fontSize="$2">makespan {plan.makespan}</Text>
        {solution.metrics.peak_resource != null ? (
          <Text
            fontSize="$2"
            color={solution.status === "invalid" ? "$red10" : "$color11"}
          >
            資源ピーク {solution.metrics.peak_resource}
            {data.resource_capacity != null ? ` / 上限 ${data.resource_capacity}` : ""}
          </Text>
        ) : null}
      </XStack>
      {solution.status === "invalid" ? (
        <Paragraph fontSize="$2" color="$red10">
          {solution.violations.find((v) => v.constraint_kind === "project_resource")
            ? "資源上限を超えています(cpm は資源を無視して最早開始に詰めるため)。priority_list / cp_sat を試してください。"
            : (solution.violations[0]?.message ?? "制約に違反しています")}
        </Paragraph>
      ) : null}
    </YStack>
  );
}
