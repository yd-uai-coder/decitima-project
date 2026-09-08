# Phase 4-8: Route Planner ページ(作業単位 4-8)

## この章のゴール

初の `src/features/optimization/route-planner/`。問題を編集 → 「解く」で経路を `GraphCanvas` に
可視化、「全アルゴリズム比較」で Dijkstra / Bellman-Ford / A* / networkx を横並び実測する。
ページは SSG のまま、認証必須(`RequireAuth`)。

- `route-planner/stores/route-planner-store.ts` ── Zustand。problem / solution / comparison + solve / compare
- `route-planner/hooks/useRoutePlanner.ts` ── 個別セレクタで購読する薄いフック
- `route-planner/components/{RouteResultCanvas,RoutePlannerPanel}.tsx`
- `app/(pages)/optimization/route-planner/page.tsx` ── SSG + `RequireAuth`
- `lib/menu-tree.ts` に「経路探索(Route Planner)」を追加(現行版)。Network Designer のエントリは Phase 5-5 で足す

**この章で作成 / 更新するファイル**: `src/features/optimization/route-planner/{stores,hooks,components}` 一式、
`src/app/(pages)/optimization/route-planner/page.tsx`。
**既存ファイルへの変更**: `src/lib/menu-tree.ts`(Optimization グループに route エントリを 1 つ追加。現行版は samples)。

対応サンプル: 上記。テストは `textbook/samples/ui/src/features/optimization/route-planner/stores/route-planner-store.test.ts`。
設計は Phase 3-6 の `benchmark-store` パターン、`Phase-0-7.md` §6.1(solve は認証必須)。

---

## 1. `route-planner-store.ts`

```typescript
// src/features/optimization/route-planner/stores/route-planner-store.ts(要点。全文は samples)
type RoutePlannerStore = {
  problem: OptimizationProblem;
  solution: CandidateSolution | null;       // solve の結果(経路つき)
  comparison: BenchmarkResponse | null;     // compare の結果(6 指標テーブル)
  solveStatus: AsyncStatus;
  compareStatus: AsyncStatus;
  error: string | null;
  setProblem: (problem) => void;            // 問題を差し替えると solution / comparison をクリア
  solve: (algorithm?) => Promise<void>;     // POST /solve(algorithm 省略で rule-based)
  compare: () => Promise<void>;             // POST /benchmark(全 route アルゴリズム)
  reset: () => void;
};
```

- **backend の 2 エンドポイントに対応する 2 つの action** ── `solve`(1 本の経路を可視化)と
  `compare`(実測を横並び)。状態も分ける(`solveStatus` / `compareStatus`)。
- Phase 3 の `benchmark-store` と同じく `ApiError` を握って `error` 文字列にする。
  TTL キャッシュ(`isCacheFresh`)は Route Planner では入れない ── 問題を編集しながら
  何度も試す使い方なので、キャッシュより「毎回叩く」方が素直。

---

## 2. `useRoutePlanner` ── 個別セレクタ

```typescript
export function useRoutePlanner() {
  const problem = useRoutePlannerStore((s) => s.problem);
  const solution = useRoutePlannerStore((s) => s.solution);
  // ... 1 フィールド 1 セレクタ
  return { problem, solution, comparison, solveStatus, compareStatus, error, setProblem, solve, compare, reset };
}
```

- **オブジェクトリテラルを 1 つのセレクタで返さない** ── 毎レンダー参照が変わって
  再描画ループになる。既存の `useBenchmark` と同じく 1 フィールド 1 セレクタ。

---

## 3. `RouteResultCanvas` ── 経路のハイライト

```tsx
// src/features/optimization/route-planner/components/RouteResultCanvas.tsx(要点)
export function RouteResultCanvas({ data, solution }) {
  const path = solution.assignments.problem_type === "route_planning" ? solution.assignments : null;
  if (solution.status === "infeasible" || !path)
    return <Paragraph color="$red10">解なし ── {solution.violations[0]?.message}</Paragraph>;
  return (
    <GraphCanvas nodes={data.nodes} edges={data.edges}
      highlightNodeIds={path.path_node_ids} highlightEdgeIds={path.path_edge_ids} />
  );
}
```

- **判別可能ユニオンの消費側の定石** ── `solution.assignments.problem_type === "route_planning"`
  で `RouteSolution` に絞る(TS が型を狭める)。
- `infeasible` なら違反メッセージを出す(負閉路 / 到達不能 / 負辺 + Dijkstra 指定)。
- 生成元アルゴリズム(`produced_by.name` / `.implementation`)を見出しに出す ── どれが選ばれたか
  分かる(rule-based selection の結果を UI で確認できる)。

---

## 4. `RoutePlannerPanel` + ページ

```tsx
// src/features/optimization/route-planner/components/RoutePlannerPanel.tsx(要点)
"use client";
export function RoutePlannerPanel() {
  const rp = useRoutePlanner();
  return (
    <YStack>
      <ProblemJsonEditor value={rp.problem} samples={ROUTE_SAMPLES} onChange={rp.setProblem} />
      <XStack>
        <StyledButton onPress={() => void rp.solve()}>解く(自動選択)</StyledButton>
        <StyledButton onPress={() => void rp.compare()}>全アルゴリズム比較</StyledButton>
      </XStack>
      {rp.solution ? <RouteResultCanvas data={...} solution={rp.solution} /> : null}
      {rp.comparison ? <BenchmarkTable entries={rp.comparison.entries} /> : null}
    </YStack>
  );
}
```

```tsx
// src/app/(pages)/optimization/route-planner/page.tsx
export default function RoutePlannerPage() {
  return <RequireAuth><RoutePlannerPanel /></RequireAuth>;
}
```

- **`BenchmarkTable`(Phase 3-7)をそのまま再利用** ── 比較表は既に「Algorithm × 6 指標」の形。
- **ページは SSG + `RequireAuth`** ── `solve` / `benchmark` は認証必須(`Phase-0-7.md` §6.1。
  Phase 3-5 で作ったログイン基盤の消費者)。データ取得はクライアント側(`apiFetch`)なので
  ページ自体は静的生成のまま(`decitima-ui/CLAUDE.md`)。
- サンプル問題(`sample-problems.ts`)は基本 / 必須経由 B・C / 負辺 の 3 つ ── それぞれ
  Dijkstra / A*(順序最適化)/ Bellman-Ford が選ばれるのをブラウザで確認できる。

---

## 5. `menu-tree.ts`(既存ファイルへの変更)

```typescript
{
  label: "Optimization",
  children: [
    { label: "アルゴリズム比較(Benchmark)", href: "/optimization/benchmark" },
    { label: "経路探索(Route Planner)", href: "/optimization/route-planner" },       // ← 追加
    // ネットワーク設計(Network Designer)は Phase 5-5 で追加
  ],
}
```

`MENU_TREE` はサイドメニュー / トップページ / 404 の 3 箇所から参照される。現行版を samples に同梱。

---

## 6. まとめ

- `route-planner-store` は solve(経路可視化)と compare(6 指標テーブル)の 2 action。
- `useRoutePlanner` は個別セレクタ(オブジェクト返しで再描画ループを避ける)。
- `RouteResultCanvas` が `GraphCanvas` に経路をハイライト。`infeasible` は違反メッセージ。
- ページは SSG + `RequireAuth`。`BenchmarkTable` は再利用。

## テスト観点(`textbook/samples/ui/src/features/optimization/route-planner/stores/route-planner-store.test.ts`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `useRoutePlannerStore` の状態遷移(solve / compare / setProblem / reset)
> - **ドライバ**: Vitest(`@vitest-environment node`)。`useRoutePlannerStore.getState()` を直接叩く
> - **スタブ**: `vi.mock("../api/route-planner")` ── `solveRoute` / `compareRoute` を差し替え。
>   実 HTTP を叩かず「成功 / 失敗でストアがどう変わるか」だけを見る

| ケース | 期待 |
| --- | --- |
| `solve` 成功 | `solveStatus == "success"` / `solution.assignments.total_weight` が入る |
| `solve` 失敗(reject) | `solveStatus == "error"` / `error` が truthy |
| `compare` 成功 | `compareStatus == "success"` / `comparison` が入る |
| `setProblem` | `solution` が null に戻る(前の結果をクリア) |

`npx vitest run src/features/optimization/route-planner` / `npx tsc --noEmit` / `npx eslint`。

---

これで **Phase 4(Route Planner)は完了**。負の重み / A* / 小 TSP / 産業ソルバートラック /
ベンチ分析 / 可視化ページまでが `route_planning` の 1 本の縦串で通った。

次は「**Phase 5 を開始する**」で **Network Designer**(最小全域木)── Phase 1 以来はじめての
新しい `problem_type` を、判別ユニオンに 1 メンバー足すところから端から端まで配線する。
Union-Find の深掘り / MST 理論(cut property・交換論法)/ Kruskal・Prim、そして 4-8 と同型の
Network Designer ページ(選んだリンクは実線、候補は破線)。
