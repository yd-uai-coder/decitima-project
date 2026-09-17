# Phase 12-4: UI(推薦カード)(作業単位 12-4)

## この章のゴール

`POST /api/v1/algorithms/recommend` を呼び出す opt-in の「推薦カード」を実装し、
6つの既存 Planner Panel すべてに1行ずつ導線を配線する。problem_type に依存しない
共通コンポーネントとして作ることがこの章の核。

**この章で作成/更新するファイル**: `ui/src/lib/api/types.ts`(改訂、型追加)、
`ui/src/features/optimization/api/recommend.ts`(新規)、
`ui/src/features/optimization/stores/recommendation-store.ts`(新規)、
`ui/src/features/optimization/hooks/useAlgorithmRecommendation.ts`(新規)、
`ui/src/features/optimization/components/AlgorithmRecommendationCard.tsx`(新規)、
6つの既存 Planner Panel(`RoutePlannerPanel.tsx`・`NetworkDesignerPanel.tsx`・
`ShiftSchedulerPanel.tsx`・`ProjectPlannerPanel.tsx`・`LogisticsPlannerPanel.tsx`・
`TravelPlannerPanel.tsx`、改訂)。

---

## 1. なぜ `features/optimization/` 直下(共通領域)に置くか

推薦機能は problem_type に依存しない ── どのドメインの問題でも同じ API・同じ UI で
表示できる。Phase 9-9 の `useJobPolling`、Phase 10 の `pending-problem-store` と同じ判断で、`features/optimization/route-planner/` のようなドメイン別ディレクトリではなく
`features/optimization/{api,stores,hooks,components}` の共通領域に置く。

## 2. 型 ── 既存 `AlgorithmMeta` を拡張する

```typescript
// ui/src/lib/api/types.ts(追記)
export type AlgorithmRecommendation = AlgorithmMeta & {
  description: string;
  is_rule_preferred: boolean;
  llm_rank?: number | null;
  llm_comment?: string | null;
};

export type RecommendationResponse = {
  problem_type: string;
  rule_preferred: string;
  recommendations: AlgorithmRecommendation[];
  notes: string[];
};
```

`AlgorithmMeta`(Phase 3、`name`/`family`/`implementation`/`time_complexity`/
`space_complexity`)を交差型で拡張する ── バックエンドの `AlgorithmRecommendation` が`AlgorithmMeta` の4フィールドをそのまま転記している設計と対応させる(12-1 参照)。

## 3. API → store → hook の3層(`useBenchmark` と同型)

```typescript
// ui/src/features/optimization/api/recommend.ts(全文)
import { apiFetch } from "@/lib/api/client";
import type { OptimizationProblem, RecommendationResponse } from "@/lib/api/types";

export function recommendAlgorithm(
  problem: OptimizationProblem,
): Promise<RecommendationResponse> {
  return apiFetch<RecommendationResponse>("/api/v1/algorithms/recommend", {
    method: "POST",
    body: JSON.stringify({ problem }),
  });
}
```

```typescript
// ui/src/features/optimization/stores/recommendation-store.ts(要点。benchmark-store と同じキャッシュ方針)
export const useRecommendationStore = create<RecommendationStore>((set, get) => ({
  result: null, status: "idle", error: null, fetchedAt: null,
  run: async (problem, options) => {
    if (!options?.force && get().status === "success" && isCacheFresh(get().fetchedAt)) return;
    set({ status: "loading", error: null });
    try {
      const result = await recommendAlgorithm(problem);
      set({ result, status: "success", error: null, fetchedAt: Date.now() });
    } catch (err) {
      set({ status: "error", error: err instanceof ApiError ? err.message : "アルゴリズム推薦に失敗しました" });
    }
  },
  reset: () => set({ result: null, status: "idle", error: null, fetchedAt: null }),
}));
```

`run(problem, options)` は benchmark の `run({problem, runs}, options)` と違い、
第一引数が直接 `OptimizationProblem`(推薦には runs のような追加パラメータが無いため)。
`isCacheFresh`/`force` は `benchmark-store` と全く同じ流用 ── 同じボタンを連打してもTTL 内なら再度 LLM を呼ばない。

`hooks/useAlgorithmRecommendation.ts` は `useBenchmark` と同じ「store の薄いラッパ」で専用テストは置かない(store 側のテストで十分)。

## 4. `AlgorithmRecommendationCard`

```tsx
// ui/src/features/optimization/components/AlgorithmRecommendationCard.tsx(要点)
export function AlgorithmRecommendationCard({ problem }: { problem: OptimizationProblem }) {
  const { result, status, error, run } = useAlgorithmRecommendation();
  return (
    <YStack ...>
      <Button disabled={status === "loading"} onPress={() => void run(problem)}>
        {status === "loading" ? <Spinner /> : "推薦してもらう"}
      </Button>
      {result?.recommendations.map((rec) => (
        <YStack key={rec.name} borderColor={rec.is_rule_preferred ? "$blue8" : "$borderColor"}>
          {/* name / implementation / is_rule_preferred バッジ / llm_rank バッジ /
              description / llm_comment / time_complexity */}
        </YStack>
      ))}
    </YStack>
  );
}
```

opt-in(ボタンを押すまで何もしない)であることをそのまま UI に反映する ── ページ表示時に自動で呼ばれることはない。`is_rule_preferred` の候補は枠線の色で、`llm_rank` が付いた候補は「LLM推薦 N位」バッジで強調する。

## 5. 各 Planner Panel への導線(1行ずつ)

6 つの panel はどれも `const xx = useXxxPlanner()` → `xx.problem` という同じ形を持つ
(`rp.problem`/`nd.problem`/`s.problem`/`pp.problem`/`lp.problem`/`tp.problem`)。
`<ProblemJsonEditor .../>` の直後に、ドメインごとの違いを吸収したまま1行だけ足す:

```tsx
<AlgorithmRecommendationCard problem={rp.problem} /> {/* (Phase 12) */}
```

**generic 化しない**(既存の6ドメイン方針 ── `decitima-ui` の feature slice は
problem_type/解の型/可視化が違うため共有しない)。ここで共有するのは
`AlgorithmRecommendationCard` という**部品**であって、各 panel 自体の構造ではない。

---

## まとめ

- 推薦機能は problem_type に依存しないため `features/optimization/` 直下の共通領域に置く(`useJobPolling`/`pending-problem-store` と同じ判断)。
- `AlgorithmMeta` を交差型で拡張し、API → store → hook → component の4層は
  `runBenchmark`/`useBenchmarkStore`/`useBenchmark`/`BenchmarkPanel` と同型に揃える。
- 6 Planner Panel への導線はそれぞれ1行ずつ(generic 化しない)。

## テスト観点(`recommend.test.ts` / `recommendation-store.test.ts`)

> **対象**: `recommendAlgorithm`(API 層)/ `useRecommendationStore`(store)
> **ドライバ**: vitest
> **スタブ**: `vi.mock("@/lib/api/client")` で `apiFetch` を、
> `vi.mock("../api/recommend")` で `recommendAlgorithm` をそれぞれ差し替える
> (`benchmark.test.ts`/`benchmark-store.test.ts` と同型)

| ケース                             | 期待                                                            |
| ------------------------------- | ------------------------------------------------------------- |
| `recommendAlgorithm(problem)`   | `{ problem }` を body に `POST /api/v1/algorithms/recommend` する |
| `run(problem)` 成功               | `status="success"`、`result` に反映                               |
| `run(problem)` 失敗               | `status="error"`、`error` にメッセージ                               |
| `run(problem)` を連続呼び出し(force無し) | TTL内なら2回目は API を叩かない。`force: true` なら叩く                       |
| `reset()`                       | `result`/`status`/`error`/`fetchedAt` が初期状態に戻る                |

`AlgorithmRecommendationCard`/`useAlgorithmRecommendation` 自体は薄いラッパ/表示専用のため専用テストは置かない(`BenchmarkPanel`/`useBenchmark` と同じ判断)。

```bash
npx vitest run src/features/optimization/api/recommend.test.ts src/features/optimization/stores/recommendation-store.test.ts
npx tsc --noEmit
npx eslint src/features/optimization
```

overlay 検証: vitest 新規 5 passed、既存 164 passed(無回帰)。`tsc --noEmit` / `eslint`
0 件。`Menu.test.tsx` の 1 件失敗は Phase 12 と無関係の既存事象(クリーンな decitima-ui HEAD 単体でも同じく失敗する ── `menu-tree.ts` 側の既知の未整合、この Phase の対応範囲外)。

---

## Phase 12 の完了

これで README §9 の3段階アルゴリズム選択のうち Step 2(Rule Engine + LLM 推薦)が
backend/UI 両方で実装された。既存 `/solve`/`/benchmark` のホットパスには一切触れて
いない(README「LLM 単独では最終決定しない」の徹底)。次の Phase は
[Phase-12-introduction.md](./Phase-12-introduction.md) §10「次のフェーズ」を参照
(Phase 13: Result Explanation)。
