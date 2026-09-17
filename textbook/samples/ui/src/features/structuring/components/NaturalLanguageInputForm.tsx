// DeciTima samples │ Phase 11(11-8)
"use client";

import { Spinner, Text, TextArea, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { useStructuring } from "../hooks/useStructuring";

/** 自然言語の入力フォーム。README §11「User → LLM」の入口。 */
export function NaturalLanguageInputForm() {
  const { text, setText, submit, status, error } = useStructuring();

  return (
    <YStack gap="$2">
      <TextArea
        value={text}
        onChangeText={setText}
        rows={4}
        placeholder="例: 5万円以内で東京を2日間旅行したい。浅草には必ず行きたい。"
        aria-label="natural-language-input"
      />
      <XStack gap="$2">
        <StyledButton
          theme="blue"
          disabled={status === "loading" || text.trim().length === 0}
          onPress={() => void submit()}
        >
          {status === "loading" ? <Spinner /> : "内容を理解する"}
        </StyledButton>
      </XStack>
      {error ? (
        <Text color="$red10" role="alert">
          {error}
        </Text>
      ) : null}
    </YStack>
  );
}
