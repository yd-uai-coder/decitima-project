// DeciTima samples │ Phase 3
"use client";

import { Button, Paragraph, Spinner, Text, YStack } from "tamagui";
import { useBenchmark } from "../hooks/useBenchmark";
import { SAMPLE_ROUTE_PROBLEM } from "../sample-problems";
import { BenchmarkComparisonChart } from "./BenchmarkComparisonChart";
import { BenchmarkTable } from "./BenchmarkTable";

/**
 * ベンチマーク画面の中核。デモ問題を選んで実行 → 比較テーブル + グループ棒を表示する。
 * データ取得はクライアント側(apiFetch)── ページは SSG のまま(decitima-ui/CLAUDE.md)。
 * 本番の問題定義入力・入力サイズ曲線は Phase 4 以降。
 */
export function BenchmarkPanel() {
  const { result, status, error, run } = useBenchmark();

  return (
    <YStack gap="$4" padding="$4" maxWidth={900}>
      <YStack gap="$1">
        <Text fontSize="$6" fontWeight="700">
          アルゴリズム比較(Benchmark)
        </Text>
        <Paragraph color="$color11">
          同じ問題を registry の全アルゴリズムで解き、実行時間・操作回数・メモリ・解の品質を
          並べます。実行時間とメモリは直接比較できますが、操作回数はアルゴリズムごとに数え方が
          違う(Dijkstra=heap pop 数、BruteForce=展開した部分パス数)ので「内部仕事量」として
          読んでください。
        </Paragraph>
      </YStack>

      <Button
        theme="blue"
        disabled={status === "loading"}
        onPress={() => void run({ problem: SAMPLE_ROUTE_PROBLEM, runs: 5 })}
      >
        {status === "loading" ? <Spinner /> : "デモ問題でベンチマークを実行"}
      </Button>

      {status === "error" ? <Text color="$red10">{error}</Text> : null}

      {result ? (
        <YStack gap="$4">
          <BenchmarkTable entries={result.entries} />
          <BenchmarkComparisonChart entries={result.entries} />
        </YStack>
      ) : null}
    </YStack>
  );
}
