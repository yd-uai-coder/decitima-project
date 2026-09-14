# Phase 10-6: decitima-ui Simulation ページ(作業単位 10-6)

## この章のゴール

`POST /api/v1/simulate` に投入し、既存 `useJobPolling`(Phase 9-9)で結果を待ち、シナリオ比較表を表示する画面を作る。Phase 4-8 / 5-5 / 6-8 / 7-7 / 8-7 / 9-9 の各ページは「単一のproblem_type を持つ画面」だったが、Simulation は base problem がどのドメインでもよい**横断画面**である ── その違いが UI の設計に直接反映される。

**この章で作成するファイル**: `ui/src/features/optimization/simulation/{api/simulate.ts,
stores/simulation-store.ts, hooks/useSimulation.ts, components/{ScenarioComparisonTable.tsx,
ScenariosJsonEditor.tsx, SimulationPanel.tsx}}`、`ui/src/app/(pages)/optimization/simulation/page.tsx`。
既存への変更(現行版は samples): `ui/src/lib/api/types.ts`、`ui/src/lib/menu-tree.ts`、
`ui/src/features/optimization/logistics-planner/components/LogisticsPlannerPanel.tsx`。

---

## 1. なぜシナリオ入力を JSON テキストエディタに統一するか

バックエンドの override が汎用 dict マージ(Phase 10-1)である以上、UI 側で「車両数を
増やすスライダー」のようなドメイン別の専用フォームを作ると、6 ドメイン分の入力コンポーネントが必要になり、README「スキーマ自体は不変」の設計方針と噛み合わなくなる。既存の`ProblemJsonEditor`(Phase 4)が base problem を JSON テキストで編集する前例に倣い、シナリオ一覧(`ScenarioOverride[]`)も同じ発想の `ScenariosJsonEditor` で編集する:

```tsx
// ui/src/features/optimization/simulation/components/ScenariosJsonEditor.tsx(要点)
export function ScenariosJsonEditor({ value, onChange }: {
  value: ScenarioOverride[];
  onChange: (scenarios: ScenarioOverride[]) => void;
}) {
  const [draft, setDraft] = useState(() => JSON.stringify(value, null, 2));
  // JSON.parse に失敗したらエラーメッセージだけ出し、直前の value は保持する
  ...
}
```

ドメイン別のシナリオビルダー(車両数スライダー等)は §スコープと非スコープ(introduction）のとおり見送り ── 需要が出た Phase で個別に追加する。

---

## 2. 型 ── `JobStatusResponse.result` を広げる(Phase 9 改訂)

バックエンドの Phase 10-4 と対になる改訂。`JobStatusResponse.result` を
`CandidateSolution | SimulationResult | null` に広げ、`SimulationRequest` / `ScenarioOverride`
/ `SensitivitySpec` / `ScenarioResult` / `SensitivityResult` / `SimulationResult` を追加する:

```typescript
// ui/src/lib/api/types.ts(要点。全文は samples)
// (Phase 9-8)
// result?: CandidateSolution | null;
// (Phase 10-4)
result?: CandidateSolution | SimulationResult | null;

export type SimulationResult = { base: ScenarioResult; scenarios: ScenarioResult[]; sensitivity?: SensitivityResult | null };
```

**既存ページへの影響**: `LogisticsPlannerPanel.tsx`(Phase 9-9)は `job.result` を
`CandidateSolution` として直接 `LogisticsRouteView` に渡していた。型が広がったことでコンパイルエラーになるため、判別のための型ガードを 1 行足す:

```tsx
// ui/src/features/optimization/logistics-planner/components/LogisticsPlannerPanel.tsx(改訂)
{job?.status === "succeeded" && job.result && "status" in job.result && data ? (
  <LogisticsRouteView data={data} solution={job.result} />
) : null}
```

`"status" in job.result` が判別式 ── `CandidateSolution` は `status` を持つが
`SimulationResult` は持たない(バックエンドの smart union と同じ、必須フィールドが重ならないという性質を TypeScript 側でも利用している)。**このページの挙動自体は変わらない**(simulate ジョブを logistics ページが扱うことはそもそも無い)── 型を広げたことで必要になったコンパイル時の安全確認が増えただけ。

---

## 3. `SimulationPanel` ── 投入とポーリングの合流

```tsx
// ui/src/features/optimization/simulation/hooks/useSimulation.ts(要点)
export function useSimulation() {
  const store = useSimulationStore();
  const { job, error: pollError } = useJobPolling(store.jobId);   // Phase 9-9 の共通フックを再利用
  return { ...store, job, pollError };
}
```

`useJobPolling`(Phase 9-9)は「problem_type に依存しない共通フック」として設計されており、`SimulationPanel` はこれを **1 行も変えずに** 再利用できる ── ジョブキューを再利用したバックエンド設計(Phase 10-4)と対応する、UI 側の「増分だけで済む」構造。

`job.result` が `CandidateSolution | SimulationResult | null` の union なので、表示前にバックエンドと同じ形の型ガードで絞り込む:

```tsx
// ui/src/features/optimization/simulation/components/SimulationPanel.tsx(要点)
function isSimulationResult(result: CandidateSolution | SimulationResult): result is SimulationResult {
  return "base" in result && "scenarios" in result;
}
```

---

## 4. `ScenarioComparisonTable` ── README の比較表そのもの

```tsx
// ui/src/features/optimization/simulation/components/ScenarioComparisonTable.tsx(要点)
export function ScenarioComparisonTable({ result, metricKeys }: { result: SimulationResult; metricKeys: string[] }) {
  const rows = [{ ...result.base, label: "base(as-is)" }, ...result.scenarios];
  return (
    <YStack gap="$2">
      {/* シナリオ × metricKeys の表(README §13 の「車両数・配送時間・コスト」表と同じ形） */}
      {result.sensitivity && (
        <Paragraph>感度分析: 閾値={result.sensitivity.threshold_value ?? "見つからず"}</Paragraph>
      )}
    </YStack>
  );
}
```

`metricKeys` はドメインごとに違う(route なら `total_weight`、project なら `makespan`)ため呼び出し側(`SimulationPanel`)が `result.base.metrics` のキーから決める ── ドメイン知識をUI 側の「表示するキーの選択」だけに閉じ、コンポーネント自体はドメイン非依存に保つ(汎用 override と同じ設計の反映)。tornado chart(グラフ描画)は本 Phase のスコープ外(introduction §6)── 感度分析の結果はテキスト要約のみ表示する。

---

## まとめ

- Simulation は横断画面 ── ドメイン別の専用フォームを増やさず、JSON テキストエディタに統一する(バックエンドの汎用 override 設計をそのまま UI に反映)。
- ポーリングは既存 `useJobPolling`(Phase 9-9)を無変更で再利用。
- `JobStatusResponse.result` の型が広がったことで、simulate ジョブを扱わない既存ページ(`LogisticsPlannerPanel`)にも型ガードの追加が必要になる ── 挙動は変わらない。

## テスト観点

> **対象**: `submitSimulation`(api クライアント)、`useSimulationStore`(投入 + 状態管理)
> **ドライバ**: 各テスト関数(Vitest、node 環境)
> **スタブ**: `apiFetch` / `submitSimulation` をモック(既存 `jobs.test.ts` /
> `network-designer-store.test.ts` と同じパターン)。コンポーネント(`.tsx`)はこの
> フィーチャ全体でユニットテスト対象外(既存ページ群と同じ規約 ── store/hook までを見る)

| ケース                                            | 期待                                           |
| ---------------------------------------------- | -------------------------------------------- |
| `submitSimulation` が `/api/v1/simulate` に POST | body に `scenarios` を含む                       |
| `submit` が成功                                   | `jobId` に投入結果が入る                             |
| `setScenarios` で入力を変える                         | 古い `jobId` がクリアされる(古いジョブのポーリングを止める)          |
| `submit` が失敗                                   | `submitStatus=="error"`、`jobId` は `null` のまま |

`npx vitest run src/features/optimization/simulation` /
`npx tsc --noEmit` / `npx eslint src/features/optimization/simulation`。

---

Phase 10 はこれで完了。次は README §20 の拡張順 ── Phase 11「LLM Problem Structuring」
(`Phase-10-introduction.md` §10「次のフェーズ」参照)。
