# Phase 3-6: 可視化基盤の選定 + src/features/optimization/ 骨格 + api 層の型付け(作業単位 3-6)

## この章のゴール

decitima-ui 側の作業。**プロジェクト初の `src/features/`** を立ち上げる ── これまで
decitima-ui はテンプレートのデモページだけだった(`decitima-ui/CLAUDE.md`「featureが1つも
無いうちは `src/features/` を先回りして作らない」)。ベンチマークがその最初の feature になる。

- 可視化ライブラリの**選定**(結論: Phase 3 は既存の手描き SVG を拡張。本格ライブラリは Phase 4)
- `src/lib/api/types.ts` に手書きの DTO 型(backend の schemas と対応)
- `src/features/optimization/{api,stores,hooks}` ── `apiFetch` 経由の呼び出し + Zustand ストア

**この章で新規作成するファイル**:
`src/features/optimization/api/benchmark.ts`、`src/features/optimization/stores/benchmark-store.ts`、
`src/features/optimization/hooks/useBenchmark.ts`、`src/features/optimization/sample-problems.ts`。
**既存ファイルへの変更**: `src/lib/api/types.ts`(benchmark DTO を追記。現行版は samples)。

対応サンプル: `samples/ui/src/features/optimization/{api/benchmark.ts,stores/benchmark-store.ts,hooks/useBenchmark.ts,sample-problems.ts}`、`samples/ui/src/lib/api/types.ts`。
テストは `samples/ui/src/features/optimization/stores/benchmark-store.test.ts`、
`samples/ui/src/features/optimization/api/benchmark.test.ts`。
設計は `Phase-0-3.md` §6.1〜§6.3。

> **`node_modules/next/dist/docs/` の該当ガイドを先に読む**(`decitima-ui/AGENTS.md`)──
> このプロジェクトの Next.js はメジャーアップデートで破壊的変更がある。ページ / コンポーネントを
> 書く前に `01-app/01-getting-started` を確認。

---

## 1. 可視化ライブラリの選定(`Phase-0-3.md` §6.3)

Phase 0 は「選定は Phase 3 / Phase 4 で行う。まず SVG 手描き or 軽量ライブラリで足りるか検討」
としていた。**Phase 3 の結論: 既存の手描き SVG(`LineChart` / `BarChart` のパターン)を
軸・凡例・対数軸・多系列に拡張する。本格的な図ライブラリ(recharts 等)は導入しない。**

| 観点 | 判断 |
| --- | --- |
| Phase 3 で描くもの | アルゴリズム比較の**グループ棒** + 入力サイズの**多系列ライン**(対数軸)。どちらも SVG 数十行で書ける |
| 制約 | react-native-web 0.21 / Tamagui 2 / React 19 / Next 16 / 全ページ SSG。多くのチャートライブラリは素の DOM を前提にしていて相性確認に spike が要る |
| プロジェクト方針 | YAGNI(依存は必要な Phase まで遅延)。既に `theme-gradients.ts` + `useHasMounted` の配色プラミングがある |
| Phase 4 | 経路図・ネットワーク図(ノード/エッジ描画)は手描きだと重い ── **そこで本格ライブラリを選ぶ** |

→ `pyproject` ならぬ `package.json` に**新しい依存を足さない**。`src/components/ui/charts/` に
汎用の軸付きチャートを 2 つ足すだけ(3-7)。

---

## 2. `src/lib/api/types.ts` ── 手書き DTO(既存ファイルへの追記)

```typescript
// src/lib/api/types.ts(現行版。AsyncStatus と 3-5 で足した TokenPair/AccessToken は残す)
export type AsyncStatus = "idle" | "loading" | "success" | "error";

// ── DeciTima backend の DTO(手書き。MVP は OpenAPI 生成しない ── Phase-0-3 §6.2)──
export type AlgorithmMeta = { name: string; family: string; implementation: string; /* ... */ };
export type OptimizationProblem = { problem_type: "route_planning"; /* ... */ };
export type BenchmarkRequest = { problem: OptimizationProblem; algorithms?: string[] | null; runs?: number; persist?: boolean };
export type BenchmarkEntry = { algorithm: AlgorithmMeta; solution_status: string; metrics: Record<string, number>;
  elapsed_ms_median: number; /* ... */ operation_count: number | null; quality_ratio: number | null };
export type BenchmarkResponse = { entries: BenchmarkEntry[]; benchmark_id: string | null };
export type BenchmarkRunRead = { id: string; problem_type: string; created_at: string; payload: { /* ... */ } };
```

- `Phase-0-3.md` §6.2: MVP は OpenAPI 自動生成を使わず**手書き**。backend の
  `app/schemas/optimization.py` / `app/domain/` とズレたら手で直す(コメントに明記)。
- `OptimizationProblem` は**ベンチ要求に必要な最小形**だけ(route_planning のみ。shift は Phase 6)。

---

## 3. feature レイヤー

### 3.1 `api/benchmark.ts` ── `apiFetch` 経由

```typescript
// src/features/optimization/api/benchmark.ts
export function runBenchmark(request: BenchmarkRequest): Promise<BenchmarkResponse> {
  return apiFetch<BenchmarkResponse>("/api/v1/benchmark", { method: "POST", body: JSON.stringify(request) });
}
export function getBenchmarkRun(id: string): Promise<BenchmarkRunRead> {
  return apiFetch<BenchmarkRunRead>(`/api/v1/benchmarks/${id}`);
}
```

`apiFetch`(`src/lib/api/client.ts`)が認証ヘッダ・401 サイレントリフレッシュ・エラーパースを
まとめて面倒みる ── feature 側は薄い関数を 2 本置くだけ。

### 3.2 `stores/benchmark-store.ts` ── Zustand + TTL キャッシュ

```typescript
// src/features/optimization/stores/benchmark-store.ts(要点)
export const useBenchmarkStore = create<BenchmarkStore>((set, get) => ({
  result: null, status: "idle", error: null, fetchedAt: null,
  run: async (request, options) => {
    if (!options?.force && get().status === "success" && isCacheFresh(get().fetchedAt)) return;
    set({ status: "loading", error: null });
    try {
      const result = await runBenchmark(request);
      set({ result, status: "success", error: null, fetchedAt: Date.now() });
    } catch (err) {
      set({ status: "error", error: err instanceof ApiError ? err.message : "ベンチマークに失敗しました" });
    }
  },
  reset: () => set({ result: null, status: "idle", error: null, fetchedAt: null }),
}));
```

- **React Query / SWR は使わない**(`decitima-ui/CLAUDE.md`)── `fetchedAt` + `isCacheFresh`
  (既定 20 秒 TTL)+ `reset` での invalidate で鮮度管理。
- ストアはコンポーネントと同じ feature 配下に colocate(`src/lib/stores/` のような集約は作らない)。
- `hooks/useBenchmark.ts` はストアの薄いラッパ(`result` / `status` / `run` だけ返す)。

### 3.3 `sample-problems.ts`

`SAMPLE_ROUTE_PROBLEM` ── backend の `build_route_problem` と同じ例題(A→E、最短 5)。
Phase 3 のベンチ画面はデモ問題を 1 つ選んで実行するだけ。本番の問題定義入力 UI は Phase 4。

---

## 4. まとめ

- 可視化は手描き SVG 拡張で通す。本格ライブラリは Phase 4(経路 / ネットワーク図)へ。
- `src/lib/api/types.ts` に手書き DTO(OpenAPI 生成は使わない)。
- 初の `src/features/optimization/` ── api / stores / hooks の 3 レイヤー。`apiFetch` +
  Zustand + TTL キャッシュという既存パターンに乗せる。

## テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - `benchmark-store.test.ts`(node env): **対象** = `useBenchmarkStore`。**ドライバ** =
>   テスト関数(store の `run` を直接呼ぶ)。**スタブ** = `vi.mock("../api/benchmark")` で
>   `runBenchmark` を差し替え(HTTP は飛ばさない)。
> - `benchmark.test.ts`(node env): **対象** = `runBenchmark` / `getBenchmarkRun`。
>   **スタブ** = `vi.mock("@/lib/api/client")` で `apiFetch` を差し替え、呼ばれた引数を検証。

| ファイル | ケース | 期待 |
| --- | --- | --- |
| store | 成功 | `status === "success"` / `result.benchmark_id` が入る |
| store | 失敗 | `status === "error"` / `error` にメッセージ |
| store | TTL 内の 2 回目 | `runBenchmark` は 1 回しか呼ばれない。`force: true` で 2 回目も呼ぶ |
| store | `reset()` | `result === null` / `status === "idle"` |
| api | `runBenchmark` | POST `/api/v1/benchmark` / body に `runs` |
| api | `getBenchmarkRun("xyz")` | GET `/api/v1/benchmarks/xyz` |

`npx vitest run src/features/optimization` / `npx tsc --noEmit`。

---

次章([Phase-3-7](./Phase-3-7.md))では、作業単位 3-7 ── 汎用の軸付きチャート 2 つと、
比較テーブル・グループ棒・入力サイズ曲線のコンポーネント、そしてベンチマークページを作る。
