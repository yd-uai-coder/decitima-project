# Phase 7-7: Travel Planner ページ(decitima-ui)(作業単位 7-7)

## この章のゴール

decitima-ui に 4 つ目の最適化画面を足す(Phase 4-8 Route Planner / Phase 5-5 Network Designer /
Phase 6-8 Shift Scheduler と同型)。訪問候補・予算・時間・好みを編集 →「プランを作る」で
Knapsack DP の結果を可視化、「比較」で DP / Greedy / BruteForce を横並び実測する。

**この章で作成 / 更新するファイル**(`decitima-ui/src/`):
`features/optimization/travel-planner/api/travel-planner.ts`、
`features/optimization/travel-planner/stores/travel-planner-store.ts`(+ `.test.ts`)、
`features/optimization/travel-planner/hooks/useTravelPlanner.ts`、
`features/optimization/travel-planner/sample-problems.ts`、
`features/optimization/travel-planner/components/{TravelPlannerPanel,TravelPlanCanvas}.tsx`、
`app/(pages)/optimization/travel-planner/page.tsx`。
**既存への変更**(現行版は samples): `src/lib/api/types.ts`(travel アーム)、
`src/lib/menu-tree.ts`(Optimization に travel エントリ)。

対応サンプル: 上記すべて。`decitima-ui/CLAUDE.md`(全ページ SSG / `src/lib/api/` 連携層)を参照。

---

## 1. `types.ts` に travel アーム(現行版)

```typescript
// src/lib/api/types.ts(追加)
export type Place = { id: string; name?: string | null; value: number; cost: number; duration: number };
export type TravelLeg = { id: string; endpoints: [string, string]; travel_cost: number; travel_time: number };
export type TravelData = {
  problem_type: "travel_planning";
  places: Place[]; legs: TravelLeg[];
  budget: number; time_budget: number;
  start?: string | null; preferences?: Record<string, number>;
};
export type TravelSolution = {
  problem_type: "travel_planning";
  selected_place_ids: string[]; visit_order: string[];
  total_value: number; total_cost: number; total_time: number;
};
// OptimizationProblem のユニオンに 1 アーム、CandidateSolution.assignments に TravelSolution を追加
```

- backend の `app/schemas/optimization.py` / `app/domain/` の手書きミラー(OpenAPI 生成しない ──
  `Phase-0-3.md` §6.2)。`Q23`: 型 = 共有層(`lib/api/`)、振る舞い(store / hooks)= feature ローカル。
- Phase 6-8 で `CandidateSolution.assignments` のユニオンアクセスを `.metrics.total_weight` に
  直したので(#16)、travel 追加で route / network / shift の store テストが壊れることはない。

---

## 2. api / store / hooks ── Route Planner の写し

```typescript
// features/optimization/travel-planner/api/travel-planner.ts
export function solveTravel(problem, algorithm?) { /* POST /api/v1/solve。省略で knapsack_dp */ }
export function compareTravel(problem, runs = 5) { /* POST /api/v1/benchmark ── 3 アルゴリズム */ }
```

- `store` は `network-designer-store` / `shift-scheduler-store` とほぼ同じ形(`problem` / `solution` /
  `comparison` / `solveStatus` / `compareStatus` / `error` + `solve` / `compare` / `setProblem` / `reset`)。
- store / hooks は **feature ローカル**(`src/features/optimization/travel-planner/`)。汎用の
  `src/components/` には置かない(`Q23` / テンプレの colocate 慣習)。
- `sample-problems.ts` は backend の `build_travel_problem` と対応(予算ゆるめ / きつめ / 好み係数付き)。

---

## 3. `TravelPlanCanvas` ── プラン可視化

```tsx
// features/optimization/travel-planner/components/TravelPlanCanvas.tsx(要点)
// place = ノード、leg = エッジ。GraphCanvas(手描き SVG。Phase 4)に:
//   - highlightNodeIds … 選んだ place(selected_place_ids)
//   - highlightEdgeIds … visit_order を閉路にした連続ペアを結ぶ leg(実線・強調)
//   - dashedEdgeIds    … 選ばれなかった候補 leg(破線)
// 下に 効用 / 費用(予算) / 時間(上限)。invalid なら費用・時間を赤 + 注記。
```

- 図ライブラリは足さない(`Phase-4-7.md` の「手描き SVG を継続」方針)。route / network と同じ
  `GraphCanvas` を使う ── travel のグラフも place 数十のデモ規模。
- **visit_order を閉路として描く**: `visit_order[i] → visit_order[(i+1) % n]` の各ペアを結ぶ leg id を
  `legByPair` から引いて `highlightEdgeIds` にする(最後は起点に戻る)。
- `status === "invalid"` なら「このプランは予算 or 時間を超えています(DP は移動費用を無視するため
  起こる)」── Phase 7 の教材の核を UI でも見せる。
- `infeasible` なら「プランを作れません」+ 最初の violation メッセージ。

`TravelPlannerPanel` は `ProblemJsonEditor`(サンプル選択 + JSON テキストエリア)+ 2 ボタン
(「プランを作る(Knapsack DP)」/「DP / Greedy / BruteForce 比較」)+ `TravelPlanCanvas` +
`BenchmarkTable`(3-7 を再利用)。ページは SSG + `RequireAuth`(Phase 3-5 の認証基盤の消費者)。

---

## 4. `menu-tree.ts`(現行版)

```typescript
// Optimization グループに 1 行
{ label: "旅行プラン(Travel Planner)", href: "/optimization/travel-planner" },
```

backend のユニオン分割と 1:1(route / network / shift / travel)。

---

## 5. まとめ

- Phase 4-8 / 5-5 / 6-8 と同型の 4 スライス目。api / store / hooks / components / page。
- `types.ts` に travel アーム(Place / TravelLeg / TravelData / TravelSolution + 各ユニオン)。
- `TravelPlanCanvas` は `GraphCanvas` を再利用 ── 選んだ地を強調、巡回順を実線、候補 leg を破線。
  invalid は費用・時間を赤で「移動費用を無視した DP の解」であることを見せる。
- generic 化しない ── problem_type / 解の型 / 可視化が違う(`Q23`)。

## テスト観点(`samples/.../travel-planner/stores/travel-planner-store.test.ts`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `useTravelPlannerStore` の `solve` / `compare` / エラー処理 / `setProblem`
> - **ドライバ**: Vitest(`@vitest-environment node`)。`getState().solve()` を直接呼ぶ
> - **スタブ**: `../api/travel-planner` を `vi.mock` ── HTTP を打たずに store のロジックだけ見る

| ケース | 期待 |
| --- | --- |
| `solve` 成功 | `solveStatus === "success"` / `solution.metrics.total_value` が入る |
| `compare` 成功 | `comparison` に BenchmarkResponse |
| `solve` 失敗 | `solveStatus === "error"` |
| `setProblem` | 前の `solution` がクリアされる |

```bash
npx tsc --noEmit
npx vitest run src/features/optimization      # travel-planner store 4 + 既存
npx eslint src/features/optimization src/lib/api/types.ts src/lib/menu-tree.ts \
  'src/app/(pages)/optimization'
```

---

Phase 7(Travel Planner)はここで完了。**4 つ目の problem_type `travel_planning`** が端から端まで
通り、DP という新パラダイム(部分問題の最適解を積み上げる)を実問題に適用した。Floyd-Warshall で
前処理した全点対距離を使い「選択(Knapsack DP)→ 巡回順(Floyd-Warshall + waypoints)」の 2 段構え、
そして「DP は移動無視の上界 / Greedy は移動込みで安全 / BruteForce が正解オラクル」という 3 者の
関係を `analysis/` で実測した。

全体の overlay 検証(backend `uv run pytest` 343 passed / ui `npx vitest` / それぞれ
ruff・eslint・tsc・pyright / `alembic upgrade head` は新テーブルなし / notebook 4 本実行)は
`samples/README.md` の手順で回す。次は README §20 の拡張順 ── **Project Manager(Phase 8、
Critical Path)**。
