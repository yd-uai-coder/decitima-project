# Phase 8-7: Project Manager ページ(decitima-ui)(作業単位 8-7)

## この章のゴール

decitima-ui に **5 スライス目** `project-planner` を足す。Phase 4-8(Route Planner)/ 7-7
(Travel Planner)と**完全に同型** ── `api` / `stores` / `hooks` / `components` /
`sample-problems.ts` / `page.tsx`。加えて **`GanttCanvas`**(ドメイン非依存のタイムラインバー)を新規に作る ── `GraphCanvas` / `GroupedBarChart` / `MultiLineChart` と並ぶ `components/ui/charts/` のチャート、テンプレート還元候補。依存 DAG は既存の `GraphCanvas` を再利用する。

> `decitima-ui` の feature slice は **generic 化しない**(`CLAUDE.md` の確定事項)── problem_type /解の型 / 可視化が違う。共有は `lib/api/` の型と `apiFetch`、そして `components/ui/charts/` のドメイン非依存チャートだけ。

**この章で作成 / 更新するファイル**(`decitima-ui/src/`):

- 新規: `features/optimization/project-planner/{api/project-planner.ts, stores/project-planner-store.ts
  (+ .test.ts), hooks/useProjectPlanner.ts, components/{ProjectPlannerPanel,ProjectGanttView}.tsx,
  sample-problems.ts}`、`components/ui/charts/GanttCanvas.tsx`、
  `app/(pages)/optimization/project-planner/page.tsx`
- 現行版: `lib/api/types.ts`(project アーム)、`lib/menu-tree.ts`(メニュー項目)

対応サンプル: `textbook/samples/ui/src/**`。`decitima-ui/CLAUDE.md` / `AGENTS.md` を先に読む(Next.js のメジャーアップデートで破壊的変更あり)。

---

## 1. `types.ts` に project アーム(現行版)

```typescript
// src/lib/api/types.ts(追加)
export type ProjectTask = { id: string; name?: string | null; duration: number; resource?: number };
export type TaskDependency = { id: string; predecessor: string; successor: string };
export type ProjectData = {
  problem_type: "project_scheduling";
  tasks: ProjectTask[]; dependencies: TaskDependency[]; resource_capacity?: number | null;
};
export type ScheduledTask = { task_id: string; start: number; finish: number; slack: number };
export type ProjectSolution = {
  problem_type: "project_scheduling";
  task_order: string[]; schedule: ScheduledTask[]; critical_path: string[]; makespan: number;
};
// OptimizationProblem のユニオンに project_scheduling を、
// CandidateSolution.assignments のユニオンに ProjectSolution を追加
```

backend の `app/schemas/optimization.py` / `app/domain/` と 1:1(OpenAPI 生成はしない ──
`Phase-0-3.md` §6.2)。`types.ts` 1 ファイルで backend との突き合わせを閉じる。

---

## 2. `GanttCanvas` ── ドメイン非依存のタイムラインバー(新規)

```tsx
// src/components/ui/charts/GanttCanvas.tsx(要点。全文は samples)
export type GanttBar = {
  id: string; label?: string | null;
  start: number; end: number;
  slack?: number;      // end からさらに右へ伸ばす「余裕」。0 なら描かない
  highlight?: boolean; // 強調(クリティカルパス上のタスク)
};

export function GanttCanvas({ bars, horizon, rowHeight = 26, width = 520 }: {...}) {
  // 手描き SVG。図ライブラリは入れない(GraphCanvas と同じ方針、Phase 4 で確定)
  // - 1 本 = 1 行。start/end で位置と長さ
  // - highlight → accent 色、それ以外 → base 色
  // - slack → バーの右に薄い延長(このタスクを何単位まで遅らせられるか)
  // - 上部に時間軸の目盛り
  // - useChartPalette / useHasMounted でテーマ対応(GraphCanvas と同じ)
}
```

- `GraphCanvas` と全く同じ作り(手描き SVG、`viewBox` + `width:100%`、`useChartPalette`)。
  ガントチャート専用ライブラリ(dhtmlx-gantt 等)は入れない ── README §16 の「本格的な図
  ライブラリは入れない」に従う。
- **ドメイン語(task / project)を型名に入れない** ── `GanttBar` は `{id, label, start, end, slack, highlight}`。
  テンプレート `next-tamagui-templates` へ還元できる形(`CLAUDE.md`「命名も還元を見越す」)。

---

## 3. `ProjectGanttView` ── DAG + ガント + クリティカルパス

```tsx
// src/features/optimization/project-planner/components/ProjectGanttView.tsx(要点)
export function ProjectGanttView({ data, solution }: { data: ProjectData; solution: CandidateSolution }) {
  const plan = solution.assignments.problem_type === "project_scheduling" ? solution.assignments : null;
  if (solution.status === "infeasible" || !plan)
    return <Paragraph color="$red10">スケジュールを組めません ── {...閉路など}</Paragraph>;

  const critical = new Set(plan.critical_path);
  const bars = plan.schedule.map((s) => ({
    id: s.task_id, label: nameById.get(s.task_id),
    start: s.start, end: s.finish, slack: s.slack, highlight: critical.has(s.task_id),
  }));
  return (
    <YStack gap="$2">
      <GraphCanvas nodes={...} edges={依存を directed で} highlightNodeIds={plan.critical_path} />
      <GanttCanvas bars={bars} />
      <Paragraph>クリティカルパス: {plan.critical_path.map(...).join(" → ")}</Paragraph>
      {/* makespan / 資源ピーク / 上限。invalid のとき赤メッセージ(cpm は資源を無視するため…) */}
    </YStack>
  );
}
```

- **依存 DAG = `GraphCanvas` 再利用**(タスク = ノード、依存 = `directed: true` の辺、クリティカルパスのタスクを `highlightNodeIds`)── travel の `TravelPlanCanvas` が `GraphCanvas` を再利用したのと同じ。
- **ガント = `GanttCanvas`**(クリティカルは `highlight`、slack は薄い延長バー)。
- `status === "invalid"` かつ `project_resource` 違反があれば、「cpm は資源を無視して最早開始に詰めるため。priority_list / cp_sat を試してください」と赤で表示 ── 教材の核を UI でも見せる。

---

## 4. api / store / hook / panel / sample-problems / page

Phase 7-7 の travel-planner と 1:1。

- `api/project-planner.ts` ── `solveProject(problem, algorithm?)` → `POST /solve` /
  `compareProject(problem, runs=5)` → `POST /benchmark`。
- `stores/project-planner-store.ts` ── zustand。`problem` / `solution` / `comparison` /
  `solveStatus` / `compareStatus` / `error` + `setProblem` / `solve` / `compare` / `reset`。
- `stores/project-planner-store.test.ts` ── `@vitest-environment node`。`solveProject` / `compareProject` を
  `vi.mock`。solve が schedule を格納 / compare が benchmark を格納 / 失敗で error / `setProblem` が前の解をクリア(travel store test と同型、4 本)。
- `hooks/useProjectPlanner.ts` ── store の薄いラッパ(個別セレクタ購読)。
- `components/ProjectPlannerPanel.tsx` ── `ProblemJsonEditor`(サンプル選択 + JSON 編集)+「スケジュールを作る」/「cp_sat で解く」/「cpm / priority_list / cp_sat 比較」ボタン +`ProjectGanttView` + `BenchmarkTable`。
- `sample-problems.ts` ── 3 サンプル(資源上限 3 / 資源制約なし / 納期 7 を課す)。backend の`build_project_problem` と対応。
- `app/(pages)/optimization/project-planner/page.tsx` ── SSG + `RequireAuth`(travel-planner と同型)。
- `lib/menu-tree.ts` ── Optimization グループに「工程管理(Project Manager)」を追加。

---

## 5. まとめ

- `project-planner` スライスは Phase 4-8 / 7-7 と 1:1(generic 化しない)。
- `GanttCanvas` は新規・ドメイン非依存 ── `components/ui/charts/` に置き、テンプレート還元候補。
- 依存 DAG は `GraphCanvas` 再利用。クリティカルパスは両方で赤強調。
- `status === "invalid"`(資源超過)を UI でも明示 ── Phase 8 の教材の核を画面で見せる。

## テスト観点(`textbook/samples/ui/src/features/optimization/project-planner/stores/project-planner-store.test.ts`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `useProjectPlannerStore`(solve / compare / setProblem / reset の状態遷移)
> - **ドライバ**: Vitest(node 環境)。store のメソッドを直接呼ぶ
> - **スタブ**: `../api/project-planner` を `vi.mock`(`solveProject` / `compareProject` をフェイクに)──
>   HTTP は叩かない。store のロジックだけを見る

| ケース                    | 期待                                                              |
| ---------------------- | --------------------------------------------------------------- |
| `solve()`(mock 成功)     | `solveStatus === "success"` / `solution.metrics.makespan === 8` |
| `compare()`(mock 成功)   | `comparison` に benchmark レスポンス                                  |
| `solve()`(mock reject) | `solveStatus === "error"`                                       |
| `setProblem()` 後       | `solution === null`(前の解がクリアされる)                                 |

`npx vitest run src/features/optimization/project-planner` / `npx tsc --noEmit` /
`npx eslint src/features/optimization/project-planner src/components/ui/charts`。

---

Phase 8 ── Project Manager はここで完了。5 つ目の problem_type `project_scheduling` がvalidate→select→solve→verify を端から端まで通り、ガントチャートで可視化できる。

overlay 検証(`textbook/samples/README.md`): Phase 7 end に Phase 8 samples を重ねて
`uv run pytest`(**405 passed, 4 deselected**)/ `ruff` / `uvx pyright` / `alembic upgrade head`
(新テーブルなし)。decitima-ui に重ねて `npx tsc --noEmit` / `npx vitest run` / `npx eslint`。

次は README §20 の拡張順 ── **Logistics(Phase 9、Vehicle / Delivery モデル、Capacity Constraint、Route + Packing + 配送順の複合最適化)**。
