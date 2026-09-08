"use client";

import { Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { BenchmarkTable } from "@/features/optimization/components/BenchmarkTable";
import { ProblemJsonEditor } from "@/features/optimization/components/ProblemJsonEditor";
import { ShiftGrid } from "@/features/optimization/shift-scheduler/components/ShiftGrid";
import { useShiftScheduler } from "@/features/optimization/shift-scheduler/hooks/useShiftScheduler";
import { SHIFT_SAMPLES } from "@/features/optimization/shift-scheduler/sample-problems";

/**
 * Shift Scheduler 画面の中核。スタッフとスロットを編集 → 「作成する」でシフト表を可視化、
 * 「比較」で Greedy / Backtracking / B&B / CP-SAT を横並び実測する。
 * 手実装は小規模で最適、規模が上がると CP-SAT が必要になる。
 */
export function ShiftSchedulerPanel() {
  const s = useShiftScheduler();
  const data = s.problem.problem_type === "shift_scheduling" ? s.problem.data : null;

  return (
    <YStack gap="$4" padding="$4" maxWidth={960}>
      <YStack gap="$1">
        <Text fontSize="$6" fontWeight="700">
          Shift Scheduler
        </Text>
        <Paragraph color="$color11">
          人件費最小化・希望休最大化・勤務時間均等化の重み付き和を、hard 制約(必要人数 / 週勤務時間 /
          連続勤務日数 / 可用性 / スキル)を守りつつ最適化します。
        </Paragraph>
      </YStack>

      <ProblemJsonEditor value={s.problem} samples={SHIFT_SAMPLES} onChange={s.setProblem} />

      <XStack gap="$2" flexWrap="wrap">
        <StyledButton
          theme="blue"
          disabled={s.solveStatus === "loading"}
          onPress={() => void s.solve()}
        >
          {s.solveStatus === "loading" ? <Spinner /> : "作成する(Backtracking)"}
        </StyledButton>
        <StyledButton
          disabled={s.solveStatus === "loading"}
          onPress={() => void s.solve("cp_sat")}
        >
          CP-SAT で作成
        </StyledButton>
        <StyledButton disabled={s.compareStatus === "loading"} onPress={() => void s.compare()}>
          {s.compareStatus === "loading" ? <Spinner /> : "4 アルゴリズム比較"}
        </StyledButton>
      </XStack>

      {s.error ? <Text color="$red10">{s.error}</Text> : null}

      {data && s.solution ? <ShiftGrid data={data} solution={s.solution} /> : null}

      {s.comparison ? <BenchmarkTable entries={s.comparison.entries} /> : null}
    </YStack>
  );
}
