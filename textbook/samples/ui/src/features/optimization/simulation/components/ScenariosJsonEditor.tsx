// DeciTima samples │ Phase 10
"use client";

import { useState } from "react";
import { Paragraph, Text, TextArea, YStack } from "tamagui";
import type { ScenarioOverride } from "@/lib/api/types";

/**
 * シナリオ一覧(`ScenarioOverride[]`)を JSON テキストで編集する簡易エディタ。
 * override は汎用 dict マージ(バックエンド `apply_overrides`、Phase 10-1)なので、
 * ドメインごとの専用フォームは作らない ── `ProblemJsonEditor`(Phase 4)と同じ考え方。
 */
export function ScenariosJsonEditor({
  value,
  onChange,
}: {
  value: ScenarioOverride[];
  onChange: (scenarios: ScenarioOverride[]) => void;
}) {
  const [draft, setDraft] = useState(() => JSON.stringify(value, null, 2));
  const [parseError, setParseError] = useState<string | null>(null);

  const applyDraft = (text: string) => {
    setDraft(text);
    try {
      const parsed = JSON.parse(text) as ScenarioOverride[];
      setParseError(null);
      onChange(parsed);
    } catch {
      setParseError("JSON として読めません");
    }
  };

  return (
    <YStack gap="$2">
      <Text fontWeight="700">シナリオ(label + overrides の配列)</Text>
      <TextArea
        value={draft}
        onChangeText={applyDraft}
        minHeight={140}
        fontFamily="$mono"
        fontSize="$2"
      />
      {parseError ? <Paragraph color="$red10">{parseError}</Paragraph> : null}
    </YStack>
  );
}
