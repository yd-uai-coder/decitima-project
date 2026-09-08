"use client";

import { Paragraph, Text, XStack, YStack } from "tamagui";
import type { CandidateSolution, ShiftData } from "@/lib/api/types";

/**
 * シフト可視化。行 = スロット(日 + 時間帯)、セル = 割り当てられたスタッフ。
 * 必要人数に満たないスロットは赤で示す(Verification が invalid にしたもの)。
 */
export function ShiftGrid({
  data,
  solution,
}: {
  data: ShiftData;
  solution: CandidateSolution;
}) {
  const shift =
    solution.assignments.problem_type === "shift_scheduling" ? solution.assignments : null;
  const assignments = shift?.assignments ?? {};

  return (
    <YStack gap="$2">
      <Text fontWeight="700">
        シフト表({solution.produced_by.name} / {solution.produced_by.implementation})
      </Text>

      {solution.status === "infeasible" || !shift ? (
        <Paragraph color="$red10">
          実行可能なシフトを作れません ──{" "}
          {solution.violations[0]?.message ?? "hard 制約を満たす割当が存在しません"}
        </Paragraph>
      ) : (
        <YStack borderWidth={1} borderColor="$borderColor" borderRadius="$3">
          {[...data.slots]
            .sort((a, b) => (a.day + a.id).localeCompare(b.day + b.id))
            .map((slot) => {
              const picked = assignments[slot.id] ?? [];
              const short = picked.length < slot.required_headcount;
              return (
                <XStack
                  key={slot.id}
                  padding="$2"
                  gap="$3"
                  borderBottomWidth={1}
                  borderColor="$borderColor"
                  backgroundColor={short ? "$red2" : undefined}
                >
                  <Text width={190} fontFamily="$mono" fontSize="$2">
                    {slot.day} {String(slot.start_hour).padStart(2, "0")}–
                    {String(slot.end_hour).padStart(2, "0")}
                  </Text>
                  <Text flex={1}>
                    {picked.length ? picked.join(", ") : "(未割当)"}
                    {short ? ` ／ 必要 ${slot.required_headcount} 人` : ""}
                  </Text>
                </XStack>
              );
            })}
        </YStack>
      )}

      {shift ? (
        <XStack gap="$4" flexWrap="wrap">
          <Metric label="人件費" value={`¥${(solution.metrics.labor_cost ?? 0).toLocaleString()}`} />
          <Metric
            label="希望休達成率"
            value={`${Math.round((solution.metrics.day_off_satisfaction ?? 0) * 100)}%`}
          />
          <Metric
            label="勤務時間の分散"
            value={(solution.metrics.hour_variance ?? 0).toFixed(1)}
          />
          <Metric label="制約違反" value={`${solution.violations.length} 件`} />
        </XStack>
      ) : null}
    </YStack>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <YStack>
      <Text fontSize="$2" color="$color11">
        {label}
      </Text>
      <Text fontWeight="700">{value}</Text>
    </YStack>
  );
}
