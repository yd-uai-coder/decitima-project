# Phase 9-9: decitima-ui ── Logistics Optimizer ページ(作業単位 9-9)

## この章のゴール

decitima-ui に **6 スライス目**(Phase 4-8 / 5-5 / 6-8 / 7-7 / 8-7 と同型)の Logistics
Optimizer 画面を追加する。車両ごとの配送ルートを可視化し、「配送計画を作る」(手実装既定 /`knapsack_dp`)・「使用台数を最小化(PuLP)」・「5 strategy を比較」・「ジョブとして投げる(`/jobs`)」の 4 操作を実演する ── Phase 9 全体(CVRP + PuLP + ジョブキュー)を UI から一望できる、Phase 9 の最終章。

**この章で作成 / 更新するファイル**: `src/features/optimization/logistics-planner/`
一式(`api/logistics-planner.ts`、`stores/logistics-planner-store.ts`、
`hooks/useLogisticsPlanner.ts`、`components/{LogisticsRouteView,LogisticsPlannerPanel}.tsx`、
`sample-problems.ts`)、`src/features/optimization/api/jobs.ts`(新規、problem_type 非依存の共通 API)、`src/features/optimization/hooks/useJobPolling.ts`(新規、共通フック)、`src/app/(pages)/optimization/logistics-planner/page.tsx`(新規)。
**既存への変更**(現行版は samples): `src/lib/api/types.ts`(`LogisticsData` 等の型追加)、`src/lib/menu-tree.ts`(Optimization グループに 1 行)。

設計は `Phase-4-8.md` / `Phase-7-7.md` / `Phase-8-7.md`(同型の feature slice 構成)。

---

## 1. `src/lib/api/types.ts` ── バックエンドの DTO を手書きで追従

```ts
// (追加。全文は samples)
export type LogisticsNode = { id: string; label?: string | null; x?: number | null; y?: number | null };
export type RoadSegment = { id: string; source: string; target: string; distance: number; directed?: boolean };
export type Vehicle = { id: string; capacity_weight: number; capacity_volume: number };
export type DeliveryStop = { id: string; node_id: string; demand_weight: number; demand_volume: number };

export type LogisticsData = {
  problem_type: "logistics_planning";
  depot_id: string;
  nodes: LogisticsNode[];
  segments: RoadSegment[];
  vehicles: Vehicle[];
  deliveries: DeliveryStop[];
};

export type VehicleRoute = { vehicle_id: string; stop_ids: string[]; distance: number };
export type LogisticsSolution = { problem_type: "logistics_planning"; routes: VehicleRoute[]; total_distance: number };

// OptimizationProblem / CandidateSolution.assignments のユニオンに非破壊で追記
```

MVP は OpenAPI 生成をしない(`Phase-0-3.md` §6.2)ので、backend の `app/schemas/optimization.py`
/ `app/domain/problems/logistics.py` とこのファイルの突き合わせは手作業 ── 既存 5 problem_typeと同じ運用。**既存メンバーには一切触れず追記だけ**(travel/project 追加時と同じ非破壊原則)。

ジョブキュー(9-8)の DTO も同じファイルに追記する:

```ts
export type JobSubmitResponse = { job_id: string; status: string };
export type JobStatusResponse = {
  job_id: string; problem_type: string;
  status: "queued" | "running" | "succeeded" | "failed";
  result?: CandidateSolution | null; problem_id?: string | null; solution_id?: string | null;
  error?: string | null; created_at: string; updated_at: string;
};
```

---

## 2. 可視化 ── `GraphCanvas` を small multiples で再利用(色分けはしない)

README の当初イメージは「車両ごとに色分けした `GraphCanvas`」だったが、`GraphCanvas` の既存 API(`highlightNodeIds` / `highlightEdgeIds` / `dashedEdgeIds`)は**単色のハイライト1系統だけ**を持つ設計で、車両 N 台ぶんの N 色を同時に塗り分ける機能は無い。ここで 2 択があった:

1. `GraphCanvas` 自体を拡張してグループごとの色分けを持たせる
2. **`GraphCanvas` は変更せず、車両ごとに 1 枚ずつ並べる**(small multiples)

**2 を選んだ**(`LogisticsRouteView.tsx`)── `GraphCanvas` はドメイン非依存のテンプレート還元候補(route/network/travel/project の 4 者が使う共有資産)であり、「1 台の色を目立たせる」だけなら既存 API(`highlightNodeIds`)で足りる。1 に手を広げる実在の消費者はこの Phase には無い(進行のルール #17)。

```tsx
// components/LogisticsRouteView.tsx(要点。全文は samples)
{plan.routes.map((route) => (
  <YStack key={route.vehicle_id}>
    <Text>車両 {route.vehicle_id} ── 距離 {route.distance}</Text>
    <GraphCanvas nodes={nodes} edges={edges} highlightNodeIds={[data.depot_id, ...訪問ノード]} />
    <Paragraph>訪問順: {route.stop_ids.join(" → ")}</Paragraph>
  </YStack>
))}
```

**もう1つのスコープ注記**: 区間(道路)の色分けもしない。API は「デポ→各配送先の訪問順」
(ノード単位)までしか返さず、2 地点間で実際にどの道路区間を通ったか(Floyd-Warshall が内部で選んだ最短経路の内訳)は返さない ── 正確な経路線を引けるのはノードまで(Phase 9 のスコープ外。README §12.5 の評価指標には影響しない)。

---

## 3. ジョブキュー(9-8)の UI ── `problem_type` 非依存の共通フック

```ts
// features/optimization/api/jobs.ts(新規、feature 共通 ── logistics 専用ではない)
export function submitJob(problem: OptimizationProblem, algorithm?: string): Promise<JobSubmitResponse> { ... }
export function getJobStatus(jobId: string): Promise<JobStatusResponse> { ... }

// features/optimization/hooks/useJobPolling.ts(新規、feature 共通)
export function useJobPolling(jobId: string | null): { job: JobStatusResponse | null; error: string | null } { ... }
```

- backend のジョブキューが problem_type に依存しない横断インフラ(9-8)なのに対応し、UI 側のこの 2 ファイルも `src/features/optimization/{api,hooks}/`(feature 直下の共通領域。
  `ProblemJsonEditor` / `BenchmarkTable` と同じ置き場)に置く ── **`logistics-planner/` の中には置かない**(Logistics 専用ではないため)。
- `useJobPolling` は 1.5 秒間隔でポーリングし、`succeeded` / `failed` に達したら自動的に止まる。**状態のリセットは effect 内で同期的に `setState` しない** ── React の
  推奨パターン(「prop の変化に応じて state を調整する」、レンダー中に比較して直す)を使う。
  effect 内での同期的な `setState` は cascading render を招くとして lint(`react-hooks/set-state-in-effect`)が検知する。

`logistics-planner-store.ts` は `jobId` / `jobStatus` を持つが、**ジョブの完了待ちそのものはストアに持たせない** ── 「投入」はストアの action(`submitAsJob`)、「監視」はコンポーネント側のフック(`useJobPolling`)という役割分担にする(ストアに `setInterval` を持たせるとテストが書きにくくなる・コンポーネントのマウント/アンマウントとの対応が取りづらくなるため)。

---

## 4. `LogisticsPlannerPanel.tsx` ── 4 操作をまとめる

```tsx
// components/LogisticsPlannerPanel.tsx(要点。全文は samples)
<StyledButton onPress={() => void lp.solve()}>配送計画を作る</StyledButton>
<StyledButton onPress={() => void lp.solve("pulp_milp")}>使用台数を最小化(PuLP)</StyledButton>
<StyledButton onPress={() => void lp.compare()}>5 strategy を比較</StyledButton>
<StyledButton onPress={() => void lp.submitAsJob("pulp_milp")}>ジョブとして投げる(/jobs)</StyledButton>
```

`ProblemJsonEditor` + `BenchmarkTable`(feature 共通コンポーネント、Phase 3 以来)をそのまま再利用 ── route/travel/project と同じ組み立て。`LOGISTICS_SAMPLES` は backend の`build_logistics_problem` fixture(容量ぎりぎりで2台に分けるしかない例)と、配送先 6 件・車両 3 台の規模を大きくした例の 2 パターン。

---

## 5. まとめ

- `GraphCanvas` / `ProblemJsonEditor` / `BenchmarkTable` を**1 バイトも変えず**再利用 ──
  Phase 9 の UI に新規プリミティブはほぼ無い(バックエンドと同じ構図)。
- ジョブキューの UI 部品(`api/jobs.ts` / `useJobPolling.ts`)は logistics 専用にせず feature共通領域に置いた ── 将来 route/travel/project 等が重い solve を非同期化したくなったときそのまま使える(実際に駆動する消費者が出た時点で、で構わない。今回は logistics が最初の消費者)。
- `GraphCanvas` の拡張(車両ごとの色分け)は見送り、small multiples で代替 ── 進行のルール#17 の判断基準どおり「今この Phase を駆動する消費者は何か」に照らした選択。

## テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
> 
> - **対象**: `logistics-planner-store`(`solve`/`compare`/`submitAsJob`/`setProblem`/`reset`)、`useJobPolling`(ポーリングの開始・停止・エラー処理)、`api/jobs.ts` / `api/logistics-planner.ts`
>   (URL・ペイロードの組み立て)
> - **ドライバ**: 各テストファイル。store は `vi.mock` で api 層を差し替え、hook は`@testing-library/react` の `renderHook` + `vi.useFakeTimers()`
> - **スタブ**: `vi.mock("../api/logistics-planner")` / `vi.mock(".../api/jobs")` で`apiFetch` の呼び出し先を完全に差し替える(実バックエンドを起動しない、Phase 3 以来のfeature テストの型)。**`useJobPolling` はフェイクタイマーと相性が悪い落とし穴がある**
>   ── `@testing-library/react` の `waitFor` は実タイマーのポーリングに依存するためフェイクタイマー環境ではデッドロックする。`vi.advanceTimersByTimeAsync` を `act()` で
>   包んで代用する(§3 コード参照)。
> - コンポーネント(`LogisticsRouteView.tsx` / `LogisticsPlannerPanel.tsx`)は route/travel/project の前例と同じく専用の Vitest は書かない(Tamagui コンポーネントの JSX 検証はこのプロジェクトのテスト方針の対象外。store・hook・api 層で挙動を保証する)。

| ケース                                     | 期待                                                           |
| --------------------------------------- | ------------------------------------------------------------ |
| `solve` が配送計画を保存                        | `solveStatus == "success"`、`solution.metrics.total_distance` |
| `compare` がベンチマーク結果を保存                  | `comparison` が一致                                             |
| `solve` 失敗時                             | `solveStatus == "error"`                                     |
| `setProblem`                            | `solution` / `jobId` をクリア                                    |
| `submitAsJob` 成功                        | `jobId` に返り値、`jobStatus == "success"`                        |
| `submitAsJob` 失敗                        | `jobStatus == "error"`、`jobId` は null のまま                    |
| `useJobPolling(null)`                   | 何もフェッチしない                                                    |
| `useJobPolling` が queued を返す間           | 1.5 秒ごとに再フェッチ                                                |
| `useJobPolling` が succeeded/failed に達する | それ以上フェッチしない                                                  |
| `useJobPolling` が失敗                     | `error` がセットされフェッチが止まる                                       |
| `submitJob` / `getJobStatus`            | 正しい URL・メソッド・body                                            |

`npx vitest run src/features/optimization/logistics-planner src/features/optimization/api/jobs.test.ts src/features/optimization/hooks/useJobPolling.test.ts` /
`npx tsc --noEmit` / `npx eslint src`。

---

Phase 9 完了。6 つ目の problem_type `logistics_planning` が backend(9-1〜9-8)・frontend(9-9)の両方で端から端まで通った。次は README §20 の拡張順どおり **Phase 10(What-if Simulation)**。
