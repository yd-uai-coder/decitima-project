# Phase 4-7: グラフ描画基盤 `GraphCanvas` + solve API 層(作業単位 4-7)

> この章から decitima-ui。コード記述前に `node_modules/next/dist/docs/` の該当ガイドを読むこと
> (`decitima-ui/AGENTS.md`。Next のメジャーアップデートは破壊的変更がある)。

## この章のゴール

Phase 3-6 §1 が「経路図・ネットワーク図(ノード / エッジ描画)は手描きだと重い ── **そこで
本格ライブラリを選ぶ**」として Phase 4 に送っていた宿題。**結論(Phase 4 で確定): 本格ライブラリ
(React Flow / recharts 等)は入れない。手描き SVG を継続拡張する。** 理由:

- Phase 4 のグラフはデモ規模(〜数十ノード)── 手描き SVG で十分軽い
- 「手実装を主軸に、境界の裏だけライブラリ」というプロジェクトの一貫性(`CLAUDE.md`)
- チャートは既に全部手描き SVG(`BarChart` / `LineChart` / `GroupedBarChart`)── パターンが揃っている

- `components/ui/charts/GraphCanvas.tsx` ── ノード / エッジ / 経路ハイライトを描く(ドメイン非依存 = 還元候補)
- `lib/api/types.ts` に route の DTO + route のみの判別ユニオン(現行版)。`network_design` アームは Phase 5-5 で足す
- `features/optimization/route-planner/api/` ── solve / benchmark 呼び出し
- `features/optimization/components/ProblemJsonEditor.tsx` ── 問題を JSON で編集する共有エディタ

**この章で新規作成するファイル**: `src/components/ui/charts/GraphCanvas.tsx` + `.test.tsx`、
`src/features/optimization/route-planner/api/route-planner.ts`、
`src/features/optimization/route-planner/sample-problems.ts`、
`src/features/optimization/components/ProblemJsonEditor.tsx`。
**既存ファイルへの変更**: `src/lib/api/types.ts`(route DTO 追加。現行版は samples 同梱)。

対応サンプル: 上記すべて。テストは `samples/ui/src/components/ui/charts/GraphCanvas.test.tsx`。
設計は `Phase-0-3.md` §6.3、`Phase-3-6.md` §1、`Phase-0-3.md` §6.2(OpenAPI 生成しない)、Q23(型は共有層 / 振る舞いは feature)。

---

## 1. `GraphCanvas`

```tsx
// src/components/ui/charts/GraphCanvas.tsx(要点。全文は samples)
export function GraphCanvas({
  nodes, edges,
  highlightNodeIds = [], highlightEdgeIds = [],   // 経路 / 選んだ MST リンク → 実線・強調色
  dashedEdgeIds = [],                             // 候補だが選ばれなかった → 破線
  width = 480, height = 320,
}) {
  const layout = _layout(nodes, width, height);   // x/y があればそのまま、無ければ円環
  // <svg>: <line>(directed は <marker> 矢印)+ <circle> + <text>(ラベル / 重み)
}
```

- **座標(`x` / `y`)があればそのまま配置、無ければ簡易円環レイアウト**(`_layout`)。
  A* 用に座標を持つ route 問題はそのまま地図的に、座標なしの問題は円環で。
- **既存チャートと同じパターン** ── `"use client"` + `useHasMounted` + `useChartPalette`
  (`theme-gradients.ts`)+ `viewBox` 自動フィット。ズーム / パンは入れない(最小)。
- **`role="img"` + `aria-label`** を付ける(テストで拾える / a11y)。
- **ドメイン非依存**(props は `{id, label?, x?, y?}` / `{id, source, target, weight?, directed?}`)
  ── `src/components/ui/` = 機能非依存のデザインシステム層。`next-tamagui-templates` への
  還元候補(`decitima-ui/CLAUDE.md`)。

---

## 2. `lib/api/types.ts` の拡張(既存ファイルへの変更)

```typescript
// src/lib/api/types.ts(要点)
export type RouteData = { problem_type: "route_planning"; nodes; edges; start; goal; allow_negative? };
export type RouteSolution = { problem_type: "route_planning"; path_node_ids; path_edge_ids; total_weight };
export type OptimizationProblem =   // 判別可能ユニオン(backend の ProblemData に対応)
  | { problem_type: "route_planning"; objectives; constraints?; data: RouteData };
export type CandidateSolution = { status; assignments: RouteSolution; metrics; violations; produced_by };
export type SolveRequest = { problem; algorithm?; persist? };
export type SolveResponse = { solution: CandidateSolution; problem_id; solution_id };
```

- **型は共有層 `lib/api/`、振る舞い(store / hooks)は feature ローカル**(Q23。backend の Q21 の
  フロント版)── 型は純粋な記述で結合ゼロ。backend の契約は 1 つで、将来の feature も同じ型を使う。
- **OpenAPI 生成はしない**(`Phase-0-3.md` §6.2)── `app/schemas/optimization.py` との突き合わせを
  この 1 ファイルに閉じる。手書きミラー。
- **ユニオンは今は route だけの 1 メンバー** ── Phase 5-5 で `network_design` アーム
  (`NetworkDesignData` / `NetworkDesignSolution`)を足す。backend の `ProblemData` /
  `SolutionData` ユニオンの分割(Phase 4 = route / Phase 5-3 = network 追加)と 1:1。
- `types.ts` は追記だが**現行版を samples に同梱**(全体を写す方が安全 ── Phase 1 の教訓)。

---

## 3. api 層 ── feature ごとの具体的な呼び出し

```typescript
// src/features/optimization/route-planner/api/route-planner.ts
export function solveRoute(problem, algorithm?): Promise<SolveResponse> {
  return apiFetch("/api/v1/solve", { method: "POST", body: JSON.stringify({ problem, algorithm, persist: false }) });
}
export function compareRoute(problem, runs = 5): Promise<BenchmarkResponse> {
  return apiFetch("/api/v1/benchmark", { method: "POST", body: JSON.stringify({ problem, runs, persist: false }) });
}
```

- **`solve` で経路つきの解、`benchmark` で比較表** ── `BenchmarkEntry` には `assignments`(経路)が
  無いので、可視化には `POST /solve` の `CandidateSolution` が要る。2 つの呼び出しは backend の
  2 エンドポイントに対応(store は 2 つの action を持つ)。
- `apiFetch`(`lib/api/client.ts`)が認証ヘッダ付与 / 401 サイレントリフレッシュ / エラーパースを
  やる ── feature の api 層は「どの URL をどの形で叩くか」だけ。
- network-designer の api(`solveNetwork` / `compareNetwork`)は Phase 5-5 で同型で足す。

---

## 4. `ProblemJsonEditor` ── 共有の問題入力

```tsx
// src/features/optimization/components/ProblemJsonEditor.tsx(要点)
export function ProblemJsonEditor({ value, samples, onChange }) {
  // サンプルボタン + JSON テキストエリア。パースできたら onChange(problem)、失敗なら role="alert"
}
```

- **Phase 4 のスコープは「可視化 + 比較」** ── ノードをドラッグで配置するようなリッチな
  作図エディタは作らない。サンプルを選ぶ + JSON を直接いじる、で割り切る
  (`Phase-4-introduction.md` §7)。
- route ページ(4-8)と network ページ(Phase 5-5)の両方が使うので
  `features/optimization/components/`(feature 内の共有)。

---

## 5. まとめ

- `GraphCanvas` = 手描き SVG。座標 or 円環レイアウト、highlight / dashed / directed 矢印。還元候補。
- 本格的な図ライブラリは入れない(Phase 4 で確定。`Phase-0-3.md` §6.3 にマーカー)。
- 型は `lib/api/types.ts`(共有層)、api 呼び出しは `features/.../api/`(feature ローカル)── Q23。
- 可視化には `POST /solve`(経路つき)、比較表には `POST /benchmark`。

## テスト観点(`samples/ui/src/components/ui/charts/GraphCanvas.test.tsx`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `GraphCanvas`(SVG を描くだけの純粋なプレゼンテーション)
> - **ドライバ**: Vitest + jsdom + `TamaguiProvider`。`render` / `container.querySelectorAll`
> - **スタブ**: `vi.mock("@tamagui/next-theme")` ── `NextThemeProvider` が `next/script` を読み
>   jsdom で解決できないため。チャートは `resolvedTheme` 文字列しか要らない(既存チャートテストと同じ)

| ケース | 期待 |
| --- | --- |
| ノード 3・エッジ 2 | `<circle>` 3 個、`<line>` 2 本 |
| directed エッジ 1 本 | `marker-end` を持つ `<line>` が 1 本 |
| `dashedEdgeIds` 指定 | `stroke-dasharray` を持つ `<line>` |

`npx vitest run src/components/ui/charts/GraphCanvas.test.tsx` / `npx tsc --noEmit` / `npx eslint`。

---

次章([Phase-4-8](./Phase-4-8.md))では、作業単位 4-8 ── Route Planner ページ。問題を編集して
「解く」で経路を `GraphCanvas` に可視化、「全アルゴリズム比較」で Dijkstra / Bellman-Ford / A* / networkx を並べる。
