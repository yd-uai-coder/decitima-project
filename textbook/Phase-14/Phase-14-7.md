# Phase 14-7: UI(比較カード)(作業単位 14-7)

## この章のゴール

`POST /api/v1/compare` を呼び出す opt-in の「比較カード」を実装し、6つの既存 Planner Panelすべてに1行ずつ導線を配線する。`/compare` は `/recommend`(Phase 12)と同じく素の
`OptimizationProblem` を受けるだけなので、Phase 13 の `ExplanationCard` のような
「先に永続化つき solve を挟む」2段階は不要 ── `AlgorithmRecommendationCard` と全く同じ1段階の形になる。

**この章で作成/更新するファイル**: `ui/src/lib/api/types.ts`(改訂、型追加)、
`ui/src/features/optimization/api/compare.ts`(新規)、
`ui/src/features/optimization/stores/comparison-store.ts`(新規)、
`ui/src/features/optimization/hooks/useComparison.ts`(新規)、
`ui/src/features/optimization/components/ComparisonCard.tsx`(新規)、
6つの既存 Planner Panel(改訂)。

---

## 1. 型 ── backend `app/schemas/comparison.py` と1:1

```typescript
// ui/src/lib/api/types.ts(追記)
export type ComparisonRequest = {
  problem: OptimizationProblem;
  algorithm?: string | null;
  llm_runs?: number;
};

export type RunOutcome = {
  status: string | null;
  metrics: Record<string, number>;
  hard_violations: number;
  soft_violations: number;
  elapsed_ms: number;
  error: string | null;
  structure_hash: string | null;
};

export type ComparisonMetrics = {
  constraint_compliance_rate_algorithm: number;
  constraint_compliance_rate_llm: number;
  optimality_avg_quality_ratio_llm: number | null;
  reproducibility_distinct_solutions_llm: number;
  execution_time_ms_algorithm: number;
  execution_time_ms_llm_median: number;
  error_rate_llm: number;
};

export type ComparisonNarrative = {
  summary: string;
  constraint_compliance_note: string;
  optimality_note: string;
  reproducibility_note: string;
  verifiability_note: string;
};

export type ComparisonResponse = {
  problem_type: string;
  algorithm_used: AlgorithmMeta;
  algorithm_result: RunOutcome;
  llm_results: RunOutcome[];
  metrics: ComparisonMetrics;
  narrative: ComparisonNarrative | null;
  notes: string[];
};
```

Phase 3 以来の「TS 型 ↔ app/schemas の突き合わせをこの1ファイルに閉じる」方針どおり、`ExplanationResponse`(Phase 13)の直後に追記する。

## 2. API → store → hook の3層(`/recommend` と同型、`/explain` より単純)

```typescript
// ui/src/features/optimization/api/compare.ts(新規、全文)
export function compareLlmVsAlgorithm(
  problem: OptimizationProblem,
  llmRuns?: number,
): Promise<ComparisonResponse> {
  return apiFetch<ComparisonResponse>("/api/v1/compare", {
    method: "POST",
    body: JSON.stringify({ problem, llm_runs: llmRuns }),
  });
}
```

```typescript
// ui/src/features/optimization/stores/comparison-store.ts(新規、要点)
export const useComparisonStore = create<ComparisonStore>((set, get) => ({
  result: null, status: "idle", error: null, fetchedAt: null,
  run: async (problem, options) => {
    if (!options?.force && get().status === "success" && isCacheFresh(get().fetchedAt)) return;
    set({ status: "loading", error: null });
    try {
      const result = await compareLlmVsAlgorithm(problem, options?.llmRuns);
      set({ result, status: "success", error: null, fetchedAt: Date.now() });
    } catch (err) {
      set({ status: "error", error: err instanceof ApiError ? err.message : "LLM比較の実行に失敗しました" });
    }
  },
  reset: () => set({ result: null, status: "idle", error: null, fetchedAt: null }),
}));
```

`recommendation-store.ts`(Phase 12)と1文字違わず同じ骨格(関数名・型・キャッシュ方針の`isCacheFresh`/`force` のみ)── `explanation-store.ts`(Phase 13)のように内部で別のAPI 呼び出しを挟む必要が無い。`hooks/useComparison.ts` も `useAlgorithmRecommendation`と同じ「store の薄いラッパ」で専用テストは置かない。

## 3. `ComparisonCard` ── 6軸の表 + ナレーション

```tsx
// ui/src/features/optimization/components/ComparisonCard.tsx(新規、要点)
export function ComparisonCard({ problem }: { problem: OptimizationProblem }) {
  const { result, status, error, run } = useComparison();
  return (
    <YStack ...>
      <Button disabled={status === "loading"} onPress={() => void run(problem, { llmRuns: 5 })}>
        {status === "loading" ? <Spinner /> : "LLM と比較する"}
      </Button>
      {result ? (
        <YStack gap="$3">
          <Text fontSize="$2" color="$color11">
            Algorithm: {result.algorithm_used.name}({result.algorithm_used.implementation}) /
            LLM Only: {result.llm_results.length}回試行
          </Text>
          <MetricsTable metrics={result.metrics} />
          {result.narrative ? (
            <YStack gap="$2">
              <Paragraph fontSize="$2">{result.narrative.summary}</Paragraph>
              <NarrativeSection label="制約遵守率" text={result.narrative.constraint_compliance_note} />
              <NarrativeSection label="最適性" text={result.narrative.optimality_note} />
              <NarrativeSection label="再現性" text={result.narrative.reproducibility_note} />
              <NarrativeSection label="検証可能性" text={result.narrative.verifiability_note} />
            </YStack>
          ) : null}
        </YStack>
      ) : null}
    </YStack>
  );
}
```

`MetricsTable` は5軸の数値(制約遵守率・最適性・再現性・実行時間・エラー率)を
ラベル+値の一覧で表示する小さな private コンポーネント。6軸目「検証可能性」は数値が無いので`ComparisonNarrative.verifiability_note`(テキスト)としてのみ表示する ──
`ComparisonMetrics` に5フィールドしか無い理由(14-5)がそのまま UI の構造に反映される。

`llmRuns: 5` を固定で渡す(ユーザーが回数を選べる UI は今回作らない)── README のスコープ(比較の仕組みを実演する)に対して、回数選択 UI は付加的な操作性の話であり、キックオフ確認(6ドメイン全部+ステートレス)より優先度が低いと判断(将来必要になれば独立した検討課題)。

## 4. 各 Planner Panel への導線

```tsx
<AlgorithmRecommendationCard problem={rp.problem} /> {/* (Phase 12) */}
<ExplanationCard problem={rp.problem} /> {/* (Phase 13) */}
<ComparisonCard problem={rp.problem} /> {/* (Phase 14) */}
```

Phase 12/13 と同じ「`xx.problem` を渡すだけ」の1行を、6 Planner Panel の
`ExplanationCard` の直後に追加する。import はアルファベット順を保つ
(`AlgorithmRecommendationCard` → `BenchmarkTable` → `ComparisonCard` →
`ExplanationCard` → `ProblemJsonEditor`)。

---

## まとめ

- `/compare` は `/recommend` と同じ「素の problem を渡すだけ」の1段階 API なので、
  UI 側も `AlgorithmRecommendationCard` 一式をそのままなぞるだけで済んだ
  (`ExplanationCard` の「先に persist solve」という余計な段階が不要)。
- これで `AlgorithmRecommendationCard`(Phase 12)・`ExplanationCard`(Phase 13)・
  `ComparisonCard`(Phase 14)という3つの横断コンポーネントが6 Panel 全てに揃う。

## テスト観点(`compare.test.ts` / `comparison-store.test.ts`)

> **対象**: `compareLlmVsAlgorithm`(API層)/ `useComparisonStore`(store)
> **ドライバ**: vitest
> **スタブ**: `vi.mock("@/lib/api/client")` で `apiFetch` を、`vi.mock("../api/compare")` で
> `compareLlmVsAlgorithm` を差し替える(`recommend.test.ts`/`recommendation-store.test.ts`
> と同型)

| ケース                                 | 期待                                                            |
| ----------------------------------- | ------------------------------------------------------------- |
| `compareLlmVsAlgorithm(problem, 3)` | `{ problem, llm_runs: 3 }` を body に `POST /api/v1/compare` する |
| `run(problem)` 成功                   | `status="success"`、`result` に応答が入る                            |
| `run(problem)` 失敗                   | `status="error"`、`error` にメッセージ                               |
| `run(problem)` を連続呼び出し(force無し)     | TTL内なら2回目は API を叩かない。`force: true` なら叩く                       |
| `run(problem, { llmRuns: 10 })`     | `compareLlmVsAlgorithm(problem, 10)` が呼ばれる                    |
| `reset()`                           | `result`/`status`/`error`/`fetchedAt` が初期状態に戻る                |

`ComparisonCard`/`useComparison` 自体は薄いラッパ/表示専用のため専用テストは置かない
(`AlgorithmRecommendationCard`/`useAlgorithmRecommendation` と同じ判断)。

```bash
npx vitest run src/features/optimization/api/compare.test.ts src/features/optimization/stores/comparison-store.test.ts
npx tsc --noEmit
npx eslint src/features/optimization
```

overlay 検証: vitest 新規6件 passed(既存回帰なし。全体 `npx vitest run` は
178 passed / 1 pre-existing failed ── `Menu.test.tsx` は Phase 13 時点から存在する
環境依存の失敗で本 Phase と無関係、クリーンな Phase 13 状態でも同じ箇所が失敗することを確認済み)。`tsc --noEmit` clean、`eslint .` 0件。

---

## Phase 14 の完了

これで README §14「LLM vs Algorithm Comparison」が backend/UI 両方で実装された。
LLM 層(Phase 11 構造化 → Phase 12 推薦 → Phase 13 説明 → Phase 14 比較)が一区切りし、README が「プロジェクトの核心的な検証テーマ」と呼ぶ実測比較の仕組みが揃った。
次の Phase は [Phase-14-introduction.md](./Phase-14-introduction.md) §11「次のフェーズ」を
参照(Phase 15: Production)。
