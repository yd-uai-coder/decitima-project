// DeciTima samples │ Phase 4
"use client";

import { useState } from "react";
import { Paragraph, Text, TextArea, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import type { OptimizationProblem } from "@/lib/api/types";

/**
 * OptimizationProblem を JSON テキストで編集する共有エディタ。
 * Phase 4 のスコープは「可視化 + 比較」なので、リッチな作図エディタは作らない
 * (サンプルを選ぶ + JSON を直接いじる)。route / network の両ページが使う。
 */
export function ProblemJsonEditor({
  value,
  samples,
  onChange,
}: {
  value: OptimizationProblem;
  samples: { label: string; problem: OptimizationProblem }[];
  onChange: (problem: OptimizationProblem) => void;
}) {
  const [draft, setDraft] = useState(() => JSON.stringify(value, null, 2));
  const [parseError, setParseError] = useState<string | null>(null);

  const applyDraft = (text: string) => {
    setDraft(text);
    try {
      const parsed = JSON.parse(text) as OptimizationProblem;
      setParseError(null);
      onChange(parsed);
    } catch {
      setParseError("JSON として読めません");
    }
  };

  const loadSample = (problem: OptimizationProblem) => {
    setDraft(JSON.stringify(problem, null, 2));
    setParseError(null);
    onChange(problem);
  };

  return (
    <YStack gap="$2">
      <XStack gap="$2" flexWrap="wrap">
        {samples.map((s) => (
          <StyledButton key={s.label} size="$2" onPress={() => loadSample(s.problem)}>
            {s.label}
          </StyledButton>
        ))}
      </XStack>
      <TextArea
        value={draft}
        onChangeText={applyDraft}
        rows={12}
        fontFamily="$mono"
        fontSize="$1"
        aria-label="problem-json"
      />
      {parseError ? (
        <Text color="$red10" role="alert">
          {parseError}
        </Text>
      ) : (
        <Paragraph fontSize="$1" color="$color11">
          problem_type = {value.problem_type}
        </Paragraph>
      )}
    </YStack>
  );
}
