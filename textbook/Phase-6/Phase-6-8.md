# Phase 6-8: Shift Scheduler ページ(decitima-ui)(作業単位 6-8)

## この章のゴール

decitima-ui に 3 つ目の最適化画面を足す(Phase 4-8 Route Planner / Phase 5-5 Network Designer と同型)。
スタッフとスロットを編集 → 「作成する」でシフト表を可視化、「4 アルゴリズム比較」で
Greedy / Backtracking / B&B / CP-SAT を横並び実測する。

**この章で新規作成するファイル**(`decitima-ui/src/`):
`features/optimization/shift-scheduler/api/shift-scheduler.ts`、
`features/optimization/shift-scheduler/stores/shift-scheduler-store.ts`(+ `.test.ts`)、
`features/optimization/shift-scheduler/hooks/useShiftScheduler.ts`、
`features/optimization/shift-scheduler/sample-problems.ts`、
`features/optimization/shift-scheduler/components/{ShiftSchedulerPanel,ShiftGrid}.tsx`、
`app/(pages)/optimization/shift-scheduler/page.tsx`。
**既存ファイルへの変更**(現行版は samples): `src/lib/api/types.ts`(shift アーム)、
`src/lib/menu-tree.ts`(Optimization に shift エントリ)、
`features/optimization/{route-planner,network-designer}/stores/*.test.ts`。

対応サンプル: 上記すべて。`decitima-ui/CLAUDE.md`(全ページ SSG / `src/lib/api/` 連携層)を参照。

---

## 1. `types.ts` に shift アーム(現行版)

```typescript
// src/lib/api/types.ts(追加)
export type Staff = { id: string; name?: string | null; hourly_wage: number;
  skills?: string[]; available_slot_ids?: string[]; requested_days_off?: string[] };
export type ShiftSlot = { id: string; day: string; start_hour: number; end_hour: number;
  required_headcount: number; required_skills?: string[] };
export type ShiftData = { problem_type: "shift_scheduling"; staff: Staff[]; slots: ShiftSlot[];
  max_weekly_hours?: number; max_consecutive_days?: number };
export type ShiftSolution = { problem_type: "shift_scheduling"; assignments: Record<string, string[]> };

// OptimizationProblem のユニオンに 1 アーム、CandidateSolution.assignments に ShiftSolution を追加
```

- backend の `app/schemas/optimization.py` / `app/domain/` の手書きミラー(OpenAPI 生成しない ──
  `Phase-0-3.md` §6.2)。`Q23`: 型 = 共有層(`lib/api/`)、振る舞い(store / hooks)= feature ローカル。
- **`CandidateSolution.assignments` に `ShiftSolution` を足すと、`.total_weight` を無条件アクセスして
  いた route / network の store テストが型エラー**になる(shift 解には `total_weight` が無い)。
  現行版として `.assignments.total_weight` → `.metrics.total_weight`(どの解型にもある)に直す(#16)。

---

## 2. api / store / hooks ── Route Planner の写し

```typescript
// features/optimization/shift-scheduler/api/shift-scheduler.ts
export function solveShift(problem, algorithm?) { /* POST /api/v1/solve。省略で backtracking */ }
export function compareShift(problem, runs = 5) { /* POST /api/v1/benchmark ── 4 アルゴリズム */ }
```

- `store` は `network-designer-store` とほぼ同じ形(`problem` / `solution` / `comparison` /
  `solveStatus` / `compareStatus` / `error` + `solve` / `compare` / `setProblem` / `reset`)。
  `solve(algorithm?)` で `?algorithm=cp_sat` を渡せる(CP-SAT で作成ボタン)。
- store / hooks は **feature ローカル**(`src/features/optimization/shift-scheduler/`)。汎用の
  `src/components/` には置かない ── shift 固有(`Q23` / テンプレの colocate 慣習)。
- `sample-problems.ts` は backend の `build_shift_problem` と対応(2 目的版 + 3 目的版)。

---

## 3. `ShiftGrid` ── シフト可視化

```tsx
// features/optimization/shift-scheduler/components/ShiftGrid.tsx(要点)
// 行 = スロット(日 + 時間帯)、セル = 割り当てられたスタッフ。
// 必要人数に満たないスロットは赤($red2)で示す(Verification が invalid にしたもの)。
// 下に metrics(人件費 / 希望休達成率 / 勤務時間の分散 / 制約違反数)を並べる。
```

- 図ライブラリは足さない(`Phase-4-7.md` §「手描き SVG を継続」の方針)。シフト表は tamagui の
  `YStack` / `XStack` の素朴なテーブルで十分(ノード/エッジ描画が要る route / network とは違う)。
- `infeasible` なら「実行可能なシフトを作れません」+ 最初の violation メッセージ。
- 比較表は `BenchmarkTable`(3-7)を再利用 ── 手実装は `_ops` あり、CP-SAT は空欄。

`ShiftSchedulerPanel` は `ProblemJsonEditor`(サンプル選択 + JSON テキストエリア)+ 3 ボタン
(「作成する(Backtracking)」/「CP-SAT で作成」/「4 アルゴリズム比較」)+ `ShiftGrid` + `BenchmarkTable`。
ページは SSG + `RequireAuth`(Phase 3-5 の認証基盤の消費者)。

---

## 4. `menu-tree.ts`(現行版)

```typescript
// Optimization グループに 1 行
{ label: "シフト作成(Shift Scheduler)", href: "/optimization/shift-scheduler" },
```

backend のユニオン分割と 1:1(route / network / shift)。

---

## 5. まとめ

- Phase 4-8 / 5-5 と同型の 3 スライス目。api / store / hooks / components / page。
- `types.ts` に shift アーム ── `CandidateSolution.assignments` に `ShiftSolution` を足すと
  route / network の store テストが `.total_weight` で型エラー → `.metrics.total_weight` に(#16)。
- `ShiftGrid` は手描きテーブル(図ライブラリなし)。人数不足のスロットは赤。
- generic 化しない ── problem_type / 解の型 / 可視化が違う(`Q23`)。

## テスト観点(`samples/.../shift-scheduler/stores/shift-scheduler-store.test.ts`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `useShiftSchedulerStore` の `solve` / `compare` / エラー処理
> - **ドライバ**: Vitest(`@vitest-environment node`)。`getState().solve()` を直接呼ぶ
> - **スタブ**: `../api/shift-scheduler` を `vi.mock` ── HTTP を打たずに store のロジックだけ見る

| ケース | 期待 |
| --- | --- |
| `solve` 成功 | `solveStatus === "success"` / `solution.metrics.labor_cost` が入る |
| `solve("cp_sat")` | `solveShift` が 2 番目の引数 `"cp_sat"` で呼ばれる |
| `compare` 成功 | `comparison` に BenchmarkResponse |
| `solve` 失敗 | `solveStatus === "error"` |

```bash
npx tsc --noEmit
npx vitest run src/features/optimization      # 17 passed(shift-scheduler store 4 + 既存)
npx eslint src/features/optimization src/lib/api/types.ts src/lib/menu-tree.ts \
  'src/app/(pages)/optimization'
```

---

Phase 6(Shift Scheduler)はここで完了。**MVP(Phase 0〜6)が完成**する ── route_planning /
network_design / shift_scheduling の 3 problem_type が端から端まで通り、手実装トラックと産業
ソルバートラックが同じ契約で並び、Benchmark と `analysis/` で「いつ切り替えるべきか」を実測できる。

全体の overlay 検証(backend `uv run pytest` 271 passed / ui `npx vitest` 17 passed / それぞれ
ruff・eslint・tsc・pyright / `alembic upgrade head` は新テーブルなし / notebook 実行)は
`samples/README.md` の手順で回す。次は README §20 の拡張順 ── **Travel Planner(Phase 7)**。
