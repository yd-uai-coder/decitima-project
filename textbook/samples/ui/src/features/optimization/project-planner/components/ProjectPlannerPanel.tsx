"use client";

import { Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { BenchmarkTable } from "@/features/optimization/components/BenchmarkTable";
import { ProblemJsonEditor } from "@/features/optimization/components/ProblemJsonEditor";
import { ProjectGanttView } from "@/features/optimization/project-planner/components/ProjectGanttView";
import { useProjectPlanner } from "@/features/optimization/project-planner/hooks/useProjectPlanner";
import { PROJECT_SAMPLES } from "@/features/optimization/project-planner/sample-problems";

/**
 * Project Manager 画面の中核。タスク・依存・資源上限を編集 → 「スケジュールを作る」で
 * トポロジカルソート + CPM の結果をガントチャートで可視化、「比較」で cpm / priority_list /
 * cp_sat / cpm_nx を横並び実測する。
 */
export function ProjectPlannerPanel() {
  const pp = useProjectPlanner();
  const data = pp.problem.problem_type === "project_scheduling" ? pp.problem.data : null;

  return (
    <YStack gap="$4" padding="$4" maxWidth={960}>
      <YStack gap="$1">
        <Text fontSize="$6" fontWeight="700">
          Project Manager
        </Text>
        <Paragraph color="$color11">
          タスクの依存関係からトポロジカルソートで実行順を決め、Critical Path Method で各タスクの
          開始・終了・余裕(slack)と全体所要(makespan)を求めます。資源上限を課すと、cpm(資源
          無視 = 下界)は超過して invalid になり、priority_list(資源 feasible な貪欲)/ cp_sat
          (厳密最適)が実行可能なスケジュールを返します。
        </Paragraph>
      </YStack>

      <ProblemJsonEditor value={pp.problem} samples={PROJECT_SAMPLES} onChange={pp.setProblem} />

      <XStack gap="$2" flexWrap="wrap">
        <StyledButton
          theme="blue"
          disabled={pp.solveStatus === "loading"}
          onPress={() => void pp.solve()}
        >
          {pp.solveStatus === "loading" ? <Spinner /> : "スケジュールを作る"}
        </StyledButton>
        <StyledButton disabled={pp.solveStatus === "loading"} onPress={() => void pp.solve("cp_sat")}>
          cp_sat で解く
        </StyledButton>
        <StyledButton disabled={pp.compareStatus === "loading"} onPress={() => void pp.compare()}>
          {pp.compareStatus === "loading" ? <Spinner /> : "cpm / priority_list / cp_sat 比較"}
        </StyledButton>
      </XStack>

      {pp.error ? <Text color="$red10">{pp.error}</Text> : null}

      {data && pp.solution ? <ProjectGanttView data={data} solution={pp.solution} /> : null}

      {pp.comparison ? <BenchmarkTable entries={pp.comparison.entries} /> : null}
    </YStack>
  );
}
