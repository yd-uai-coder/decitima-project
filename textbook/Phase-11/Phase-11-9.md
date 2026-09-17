# Phase 11-9: UI ── 6ドメインページへの確定連携配線(作業単位 11-9)

## この章のゴール

11-8 で作った `usePendingProblemHydration` を6つのドメイン Panel コンポーネントに1行ずつ配線し、README §11「User Confirmation → Optimization」の遷移を完成させる。Phase 11 の最終章。

**この章で作成/更新するファイル**: `RoutePlannerPanel.tsx`・NetworkDesignerPanel.tsx`・`ShiftSchedulerPanel.tsx`・`TravelPlannerPanel.tsx`・`ProjectPlannerPanel.tsx`・
`LogisticsPlannerPanel.tsx`(いずれも現行版、各1行)。

---

## 1. なぜ `page.tsx` ではなく Panel コンポーネントに配線するか

各ドメインページ(`app/(pages)/optimization/<domain>/page.tsx`)は
`<RequireAuth><XxxPlannerPanel /></RequireAuth>` だけの薄いサーバコンポーネントで、`"use client"` が無い。`usePendingProblemHydration` は `useEffect` を使うフックなので、クライアントコンポーネント側(各 `XxxPlannerPanel.tsx`、既に `"use client"`)で呼ぶ必要がある。

---

## 2. 配線パターン(6ページ共通、1行)

```tsx
// features/optimization/travel-planner/components/TravelPlannerPanel.tsx(差分)
import { usePendingProblemHydration } from "@/features/optimization/hooks/usePendingProblemHydration";
// ...
export function TravelPlannerPanel() {
  const tp = useTravelPlanner();
  usePendingProblemHydration("travel_planning", tp.setProblem); // (Phase 11-9)
  const data = tp.problem.problem_type === "travel_planning" ? tp.problem.data : null;
  // ...
```

全6ページが同じ `use*Planner()` フック → `.setProblem` の形を持つため(Phase 4〜9 で確立済みのパターン)、配線は機械的:

| ページ                         | フック変数 | problem_type           |
| --------------------------- | ----- | ---------------------- |
| `RoutePlannerPanel.tsx`     | `rp`  | `"route_planning"`     |
| `NetworkDesignerPanel.tsx`  | `nd`  | `"network_design"`     |
| `ShiftSchedulerPanel.tsx`   | `s`   | `"shift_scheduling"`   |
| `TravelPlannerPanel.tsx`    | `tp`  | `"travel_planning"`    |
| `ProjectPlannerPanel.tsx`   | `pp`  | `"project_scheduling"` |
| `LogisticsPlannerPanel.tsx` | `lp`  | `"logistics_planning"` |

`usePendingProblemHydration` はマウント時に一度だけ `consumePending(problemType)` を呼び、一致する pending があれば `setProblem` する(11-8 参照)。既存のサンプル問題読み込み(`use*Planner()` の初期 state)には一切触れない ── pending が無ければ何も起きず、従来通りサンプル問題が表示される。

---

## 3. `メニュー` への追加(11-8 で実施済みの確認)

`lib/menu-tree.ts`(11-8 で更新)に Structuring ページへのリンクを追加済み:

```ts
{ label: "自然言語で問題を作る(AI)", href: "/optimization/structuring" },
```

これで README §11 の一連(自然言語入力 → 確認 → 修正 → 確定 → 該当ドメインページで可視化・最適化)がメニューから辿れる。

---

## まとめ

- 配線は各ページ1行、6ページで完結する最小の変更(Phase 10 の `LogisticsPlannerPanel.tsx`への型ガード追加と同じ粒度)。
- `page.tsx` ではなく Panel コンポーネント(クライアント境界の内側)に配線する ── フック(`useEffect`)はサーバコンポーネントでは呼べないため。
- 既存の各ページのロジック(solve/compare/ジョブポーリング等)には一切触れない。

## テスト観点

> **対象**: 6 Panel コンポーネントへの統合
> **ドライバ**: 既存の各ページのテスト(あれば)/ 手動確認
> **スタブ**: 不要 ── 各ページへの統合は smoke レベルに留め、既存ページのテストは無改造のまま維持する(`usePendingProblemHydration` 自体の振る舞いは11-8で検証済み)

| 確認項目                            | 期待                                                   |
| ------------------------------- | ---------------------------------------------------- |
| Structuring ページで「この条件で最適化する」を押す | 該当ドメインページへ遷移し、確認カードの内容が `ProblemJsonEditor` に反映されている |
| pending が無い状態でドメインページに直接アクセス    | 従来通りサンプル問題が表示される(回帰なし)                               |
| 既存の各ドメインページのテスト一式(Phase 4〜9)    | 無改造のまま green(回帰なし)                                   |

```bash
npx tsc --noEmit
npx vitest run src/features/optimization src/features/structuring
npx eslint src/features/optimization src/features/structuring "src/app/(pages)/optimization"
```

---

## Phase 11 の完了

これで README パイプライン図の最初の矢印(自然言語 → LLM → Structured Problem →
Validation → Human-in-the-loop 確認 → Algorithm Engine)が backend/UI 両方で実装された。
次の Phase は [Phase-11-introduction.md](./Phase-11-introduction.md) §10「次のフェーズ」
を参照(Phase 12: Algorithm Recommendation)。
