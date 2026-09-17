// DeciTima samples │ Phase 11(11-8: カード本体 / 11-9: 確定ボタンの遷移先は共有 store)
"use client";

import { useRouter } from "next/navigation";
import { Paragraph, Text, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { ProblemJsonEditor } from "@/features/optimization/components/ProblemJsonEditor";
import { usePendingProblemStore } from "@/features/optimization/stores/pending-problem-store";
import { useStructuring } from "../hooks/useStructuring";
import { PROBLEM_TYPE_ROUTES, summarize } from "./domainSummaries";

/**
 * README §11 の確認カード(「AIが理解した問題」)。要約 → 必要なら `ProblemJsonEditor` で
 * 手直し(「修正する」)→「この条件で最適化する」で該当ドメインページへ遷移する。
 * 新しい solve ビューアはここでは作らず、既存の各ドメインページ(Phase 4〜9)を再利用する。
 */
export function StructuredProblemCard() {
  const { problem, notes, setProblem } = useStructuring();
  const router = useRouter();
  const setPending = usePendingProblemStore((s) => s.setPending);

  if (!problem) return null;

  const confirm = () => {
    setPending(problem);
    router.push(PROBLEM_TYPE_ROUTES[problem.problem_type]);
  };

  return (
    <YStack gap="$3" padding="$4" borderWidth={1} borderColor="$borderColor" borderRadius="$4">
      <Text fontSize="$5" fontWeight="700">
        AIが理解した条件
      </Text>

      <YStack gap="$1">
        {summarize(problem).map((item) => (
          <XStack key={item.label} gap="$2">
            <Text fontWeight="600">{item.label}:</Text>
            <Text>{item.value}</Text>
          </XStack>
        ))}
      </YStack>

      {notes.length > 0 ? (
        <YStack gap="$1">
          {notes.map((note) => (
            <Paragraph key={note} fontSize="$1" color="$color11">
              注記: {note}
            </Paragraph>
          ))}
        </YStack>
      ) : null}

      <ProblemJsonEditor value={problem} samples={[]} onChange={setProblem} />

      <XStack gap="$2">
        <StyledButton theme="green" onPress={confirm}>
          この条件で最適化する
        </StyledButton>
      </XStack>
    </YStack>
  );
}
