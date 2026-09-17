# Phase 13-4: UI(説明カード)(作業単位 13-4)

## この章のゴール

`POST /api/v1/solutions/{solution_id}/explain` を呼び出す opt-in の「説明カード」を実装し、
6つの既存 Planner Panel すべてに1行ずつ導線を配線する。**explain が `solution_id`(永続化済みの
解)を要求するのに対し、各 Panel の「解く」は `persist: false` で永続化しない**という既存方針と
の衝突をどう解決するかが、この章の核。

**この章で作成/更新するファイル**: `ui/src/lib/api/types.ts`(改訂、型追加)、
`ui/src/features/optimization/api/solve.ts`(新規)、
`ui/src/features/optimization/api/explain.ts`(新規)、
`ui/src/features/optimization/stores/explanation-store.ts`(新規)、
`ui/src/features/optimization/hooks/useSolutionExplanation.ts`(新規)、
`ui/src/features/optimization/components/ExplanationCard.tsx`(新規)、
6つの既存 Planner Panel(`RoutePlannerPanel.tsx`・`NetworkDesignerPanel.tsx`・
`ShiftSchedulerPanel.tsx`・`ProjectPlannerPanel.tsx`・`LogisticsPlannerPanel.tsx`・
`TravelPlannerPanel.tsx`、改訂)。

---

## 1. 衝突 ── explain は `solution_id` を要るが、UI の「解く」は永続化しない

各 Planner Panel の `api/<domain>-planner.ts`(例: `route-planner.ts`)を見ると:

```typescript
// ui/src/features/optimization/route-planner/api/route-planner.ts(既存、抜粋)
export function solveRoute(problem, algorithm) {
  const body: SolveRequest = { problem, algorithm: algorithm ?? null, persist: false };
  return apiFetch<SolveResponse>("/api/v1/solve", { method: "POST", body: JSON.stringify(body) });
}
```

**6ドメインすべての「解く」ボタンは `persist: false`**(編集中の探索的な試行を DB に残さない、
Phase 4 以来の既存方針)。つまり画面上の `rp.solution` は `solution_id` を持たず、explain を
そのままでは呼べない。

**この章で採る解決策**: 各 Panel の既存「解く」ボタンには一切触れず、`ExplanationCard` 専用の
**永続化つき solve**(`persist: true`)を別に用意する。「説明してもらう」を押した瞬間に
① solve(persist: true)→ solution_id 取得 ② explain(solution_id)、という2段階を
`ExplanationCard` の内部(store)で完結させる ── `AlgorithmRecommendationCard`(Phase 12、
`problem` を渡すだけ)より1段階多いが、Panel 側からは同じ「`problem` を渡すだけ」の
インターフェースに見える。

```typescript
// ui/src/features/optimization/api/solve.ts(新規、全文)
export function persistSolve(problem: OptimizationProblem, algorithm?: string): Promise<SolveResponse> {
  const body = { problem, algorithm: algorithm ?? null, persist: true };
  return apiFetch<SolveResponse>("/api/v1/solve", { method: "POST", body: JSON.stringify(body) });
}
```

`solveRoute`(`persist: false`、既存6ファイル)とは**別のファイル**(`features/optimization/
api/solve.ts`、problem_type に依存しない共通領域)に置く ── 既存の探索的な「解く」の挙動を
1行も変えないため。

## 2. 型 ── `ExplanationResponse`(README §13 の5項目 + メタ情報)

```typescript
// ui/src/lib/api/types.ts(追記)
export type ExplanationResponse = {
  solution_id: string;
  problem_type: string;
  algorithm_name: string;
  why_this_solution: string;
  key_constraints: string;
  algorithm_rationale: string;
  alternatives_comparison: string;
  improvement_notes: string;
  notes: string[];
};
```

backend `app/schemas/explanation.py::ExplanationResponse` とフィールド名を1:1で対応させる
(Phase 3 以来の「TS 型 ↔ app/schemas の突き合わせをこの1ファイルに閉じる」方針)。

## 3. API → store → hook の3層(explain だけ solve を挟む点が Phase 12 と異なる)

```typescript
// ui/src/features/optimization/api/explain.ts(新規、全文)
export function explainSolution(solutionId: string): Promise<ExplanationResponse> {
  return apiFetch<ExplanationResponse>(`/api/v1/solutions/${solutionId}/explain`, { method: "POST" });
}
```

```typescript
// ui/src/features/optimization/stores/explanation-store.ts(要点。recommendation-store と同じキャッシュ方針)
export const useExplanationStore = create<ExplanationStore>((set, get) => ({
  result: null, status: "idle", error: null, fetchedAt: null,
  run: async (problem, options) => {
    if (!options?.force && get().status === "success" && isCacheFresh(get().fetchedAt)) return;
    set({ status: "loading", error: null });
    try {
      const solved = await persistSolve(problem, options?.algorithm);
      if (!solved.solution_id) throw new ApiError(500, "解が永続化されませんでした");
      const result = await explainSolution(solved.solution_id);
      set({ result, status: "success", error: null, fetchedAt: Date.now() });
    } catch (err) {
      set({ status: "error", error: err instanceof ApiError ? err.message : "解の説明生成に失敗しました" });
    }
  },
  reset: () => set({ result: null, status: "idle", error: null, fetchedAt: null }),
}));
```

`run(problem, options)` のシグネチャは `recommendation-store` の `run(problem, options)` と
同じ ── コンポーネント側から見ると「`problem` を渡して呼ぶだけ」という点は変わらない。
違いは store の**中で** solve → explain の2段階を踏むこと。`persistSolve` が失敗すれば
その時点で `catch` に落ち、`explainSolution` は呼ばれない(呼び出し順に依存した自然な失敗
伝播 ── 追加のエラー分岐は書かない)。

`isCacheFresh`/`force` は `recommendation-store`/`benchmark-store` と全く同じ流用。
`hooks/useSolutionExplanation.ts` は `useAlgorithmRecommendation` と同じ「store の薄いラッパ」
で専用テストは置かない(store 側のテストで十分)。

## 4. `ExplanationCard`

```tsx
// ui/src/features/optimization/components/ExplanationCard.tsx(要点)
export function ExplanationCard({ problem, algorithm }: { problem: OptimizationProblem; algorithm?: string }) {
  const { result, status, error, run } = useSolutionExplanation();
  return (
    <YStack ...>
      <Button disabled={status === "loading"} onPress={() => void run(problem, { algorithm })}>
        {status === "loading" ? <Spinner /> : "この解を説明してもらう"}
      </Button>
      {result ? (
        <YStack gap="$3">
          <Text fontSize="$2" color="$color11">
            {result.algorithm_name} で計算された解(solution_id: {result.solution_id})
          </Text>
          <ExplanationSection label="なぜこの解になったか" text={result.why_this_solution} />
          <ExplanationSection label="どの制約が重要だったか" text={result.key_constraints} />
          <ExplanationSection label="どのアルゴリズムを使ったか" text={result.algorithm_rationale} />
          <ExplanationSection label="他の候補との違い" text={result.alternatives_comparison} />
          <ExplanationSection label="改善余地" text={result.improvement_notes} />
        </YStack>
      ) : null}
    </YStack>
  );
}
```

README §13 の説明対象5項目を、見出し付きの `ExplanationSection`(ファイル内の小さな private
コンポーネント)でそのまま列挙する ── `AlgorithmRecommendationCard` がバッジ・枠線色で
情報を圧縮したのとは対照的に、Result Explanation は文章そのものが価値なので装飾を足さない。

## 5. 各 Planner Panel への導線(1行ずつ、`AlgorithmRecommendationCard` の隣)

```tsx
<AlgorithmRecommendationCard problem={rp.problem} /> {/* (Phase 12) */}
<ExplanationCard problem={rp.problem} /> {/* (Phase 13) */}
```

6 つの panel はどれも Phase 12 と同じ `xx.problem` の形を再利用できる(`rp.problem`/
`nd.problem`/`s.problem`/`pp.problem`/`lp.problem`/`tp.problem`)。**generic 化しない**
(既存の6ドメイン方針)。ここで共有するのは `ExplanationCard` という**部品**であって、
各 panel 自体の構造ではない ── Phase 12 §5 と同じ判断。

---

## まとめ

- explain は `solution_id` を要るが、既存「解く」は `persist: false` ── `ExplanationCard`
  専用の `persistSolve`(新規、別ファイル)で吸収し、既存の「解く」ボタンには一切触れない。
- API → store → hook → component の4層は `AlgorithmRecommendationCard` 一式と同型だが、
  store 内部が solve → explain の2段階を踏む点だけが異なる。
- 6 Planner Panel への導線はそれぞれ1行ずつ(generic 化しない)。

## テスト観点(`solve.test.ts` / `explain.test.ts` / `explanation-store.test.ts`)

> **対象**: `persistSolve`/`explainSolution`(API 層)/ `useExplanationStore`(store)
> **ドライバ**: vitest
> **スタブ**: `vi.mock("@/lib/api/client")` で `apiFetch` を、`vi.mock("../api/solve")`/
> `vi.mock("../api/explain")` でそれぞれ差し替える(`recommend.test.ts`/
> `recommendation-store.test.ts` と同型)

| ケース | 期待 |
| --- | --- |
| `persistSolve(problem)` | `{ problem, persist: true }` を body に `POST /api/v1/solve` する |
| `explainSolution("s1")` | `POST /api/v1/solutions/s1/explain` する |
| `run(problem)` 成功 | `persistSolve` → `explainSolution` の順で呼ばれ、`status="success"` |
| `persistSolve` が `solution_id: null` を返す | `explainSolution` は呼ばれず `status="error"` |
| `explainSolution` が失敗 | `status="error"`、`error` にメッセージ |
| `run(problem)` を連続呼び出し(force無し) | TTL内なら2回目は API を叩かない。`force: true` なら叩く |
| `reset()` | `result`/`status`/`error`/`fetchedAt` が初期状態に戻る |

`ExplanationCard`/`useSolutionExplanation` 自体は薄いラッパ/表示専用のため専用テストは
置かない(`AlgorithmRecommendationCard`/`useAlgorithmRecommendation` と同じ判断)。

```bash
npx vitest run src/features/optimization/api/solve.test.ts src/features/optimization/api/explain.test.ts src/features/optimization/stores/explanation-store.test.ts
npx tsc --noEmit
npx eslint src/features/optimization
```

overlay 検証: vitest 77 passed(既存回帰なし、新規 solve/explain/explanation-store の 9 テスト
含む)。`tsc --noEmit` / `eslint` 0 件。

---

## Phase 13 の完了

これで README §13「Result Explanation」が backend/UI 両方で実装された。Phase 0 で敷いた
説明可能性(NFR-4)── すべての `CandidateSolution` が持つ `produced_by`/`metrics`/`violations`
── がここで人間向けの説明文として回収された。次の Phase は
[Phase-13-introduction.md](./Phase-13-introduction.md) §10「次のフェーズ」を参照
(Phase 14: LLM vs Algorithm Comparison)。
