# Phase 5-5: Network Designer ページ(作業単位 5-5)

## この章のゴール

`src/features/optimization/network-designer/`。Phase 4-8 の Route Planner と**同じ形**で、
`network_design`(最小全域木)を扱う。拠点と敷設可能リンクを編集 → 「設計する」で MST を
`GraphCanvas` に可視化(選んだリンクは実線、候補は破線)、「比較」で Kruskal / Prim / networkx を並べる。

- `network-designer/api/network-designer.ts` ── `solveNetwork` / `compareNetwork`(Phase 4-7 の route api と同型)
- `network-designer/{stores,hooks,components}` ── Phase 4-8 の route-planner と同型
- `components/MstResultCanvas.tsx` ── 選択リンク実線 + 候補破線
- `app/(pages)/optimization/network-designer/page.tsx` ── SSG + `RequireAuth`
- `network-designer/sample-problems.ts` ── `NETWORK_SAMPLES`

**この章で作成 / 更新するファイル**: `src/features/optimization/network-designer/{api,stores,hooks,components,sample-problems.ts}` 一式、
`src/app/(pages)/optimization/network-designer/page.tsx`。
**既存ファイルへの変更**(現行版は samples): `src/lib/api/types.ts`(`network_design` アームを
判別ユニオンに追加 ── `NetworkDesignData` / `NetworkDesignSolution`、`CandidateSolution.assignments`
を `RouteSolution | NetworkDesignSolution` に)、`src/lib/menu-tree.ts`(Optimization グループに
「ネットワーク設計(Network Designer)」エントリを追加)。

対応サンプル: 上記。テストは `textbook/samples/ui/src/features/optimization/network-designer/stores/network-designer-store.test.ts`。
設計は Phase 4-8(Route Planner ページ)と同じ。backend のユニオン分割(Phase 4 = route / Phase 5-3 = network 追加)と 1:1。

---

## 1. store / hook ── Phase 4-8 の写し

```typescript
// src/features/optimization/network-designer/stores/network-designer-store.ts
// route-planner-store と構造は同一。api だけ solveNetwork / compareNetwork に差し替え。
// solve の既定 algorithm は kruskal(rule-based selection)。

// src/features/optimization/network-designer/hooks/useNetworkDesigner.ts
// useRoutePlanner と同じく個別セレクタで購読する薄いラッパ。
```

- **route-planner-store と 90% 同じ** ── `problem` / `solution` / `comparison` / `solveStatus` /
  `compareStatus` / `error` / `setProblem` / `solve` / `compare` / `reset`。違いは:
  - api が `solveNetwork` / `compareNetwork`(`network-designer/api/network-designer.ts`、この章で作成)
  - デフォルト問題が `NETWORK_SAMPLES[0]`(5 拠点、MST コスト 10)
- **なぜ共通化しないのか**(1 つの generic な store にしない): route と network は
  `problem_type` が違い、`assignments` の型も違い(`RouteSolution` / `NetworkDesignSolution`)、
  可視化コンポーネントも別。無理に共通化すると分岐だらけになる ── 「一緒に変わるものを
  同じファイルに」(`Phase-0-2.md` §2.5)。共有するのは api 層の下(`apiFetch`)と型
  (`lib/api/types.ts`)だけ。

---

## 2. `MstResultCanvas`

```tsx
// src/features/optimization/network-designer/components/MstResultCanvas.tsx(要点)
export function MstResultCanvas({ data, solution }) {
  const mst = solution.assignments.problem_type === "network_design" ? solution.assignments : null;
  const edges = data.links.map((l) => ({ id: l.id, source: l.endpoints[0], target: l.endpoints[1], weight: l.weight }));
  const selected = new Set(mst?.selected_link_ids ?? []);
  return (
    <GraphCanvas nodes={data.nodes} edges={edges}
      highlightEdgeIds={mst.selected_link_ids}                              // 選んだ → 実線・強調
      dashedEdgeIds={edges.filter((e) => !selected.has(e.id)).map((e) => e.id)} />  // 候補 → 破線
  );
}
```

- **`NetworkLink.endpoints`(tuple)→ `GraphCanvas` の `{source, target}` に変換** ── リンクは
  無向なので `directed` は付けない(矢印なし)。
- **候補リンクを破線で残す**のが Route Planner との違い ── 「この候補集合から、この部分集合を
  選んだ」が一目で分かる(README §12.6 の図そのもの)。
- `infeasible` なら違反メッセージ(候補リンクで全拠点が繋がらない / 必須リンクが閉路)。

---

## 3. `NetworkDesignerPanel` + ページ

```tsx
// src/features/optimization/network-designer/components/NetworkDesignerPanel.tsx(要点)
"use client";
export function NetworkDesignerPanel() {
  const nd = useNetworkDesigner();
  return (
    <YStack>
      <ProblemJsonEditor value={nd.problem} samples={NETWORK_SAMPLES} onChange={nd.setProblem} />
      <XStack>
        <StyledButton onPress={() => void nd.solve()}>設計する(Kruskal)</StyledButton>
        <StyledButton onPress={() => void nd.compare()}>Kruskal / Prim / networkx 比較</StyledButton>
      </XStack>
      {nd.solution ? <MstResultCanvas data={...} solution={nd.solution} /> : null}
      {nd.comparison ? <BenchmarkTable entries={nd.comparison.entries} /> : null}
    </YStack>
  );
}
```

```tsx
// src/app/(pages)/optimization/network-designer/page.tsx
export default function NetworkDesignerPage() {
  return <RequireAuth><NetworkDesignerPanel /></RequireAuth>;
}
```

- `ProblemJsonEditor`(Phase 4-7)/ `BenchmarkTable`(3-7)を再利用。
- サンプルは「5 拠点(コスト 10)」と「必須 L_ac・禁止 L_bc」── 制約が MST に効くのを確認できる。
- **`src/features/optimization/` が 3 画面になる** ── benchmark(比較専用、Phase 3)/
  route-planner(Phase 4)/ network-designer(この章)。それぞれ独立した slice
  (`{api, stores, hooks, components}`)。

---

## 4. まとめ

- `network-designer` は `route-planner` と同型の slice(store / hook / panel / result canvas)。
- 無理に generic 化しない ── problem_type / 解の型 / 可視化が違う。共有は api 層の下と型だけ。
- `MstResultCanvas` は選んだリンク実線 + 候補破線(README §12.6 の図)。
- `types.ts` / `menu-tree.ts` に network アームを足す ── backend のユニオン分割と 1:1。
- `features/optimization/` が benchmark / route-planner / network-designer の 3 画面に。

## テスト観点(`textbook/samples/ui/src/features/optimization/network-designer/stores/network-designer-store.test.ts`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `useNetworkDesignerStore` の状態遷移
> - **ドライバ**: Vitest(node env)。`getState()` を直接叩く
> - **スタブ**: `vi.mock("../api/network-designer")` ── `solveNetwork` / `compareNetwork` を差し替え

| ケース | 期待 |
| --- | --- |
| `solve` 成功 | `solveStatus == "success"` / `solution.assignments.total_weight == 10` |
| `compare` 成功 | `comparison` が入る |
| `solve` 失敗 | `solveStatus == "error"` |

`npx vitest run src/features/optimization/network-designer` / `npx tsc --noEmit` / `npx eslint`。

---

Phase 5(Network Designer)はここで完了。全体の overlay 検証(backend `uv run pytest` 217 passed /
ui `npx vitest` 16 passed / それぞれ ruff・eslint・tsc・pyright / `alembic upgrade head` は no-op /
notebook 実行)は `samples/README.md` の手順で回す。**ここまでで MVP のアルゴリズム側は
route_planning / network_design の 2 problem_type が端から端まで通った。**

次は「Phase 6 を開始する」── Shift Scheduler(Greedy / Backtracking / Branch and Bound、
多目的の重み付き評価器、**手実装の破綻 → OR-Tools CP-SAT トラック**)。Phase 4 / 5 で
「同じインターフェースの下に手実装と `library:*` を並べてベンチで比べる」枠組みが動いているので、
Phase 6 の「いつソルバーに切り替えるべきか」を `analysis/shift_analysis.py` の実測で示せる。
