# Phase 3-7: 比較テーブル + 入力サイズ曲線チャート + ページ(作業単位 3-7)

## この章のゴール

decitima-ui のベンチマーク画面を完成させる。汎用の軸付きチャートを 2 つ
(`src/components/ui/charts/`、ドメイン非依存 = テンプレート還元候補)、それを使う
feature コンポーネント、そして SSG ページ。

**この章で新規作成するファイル**:
`src/components/ui/charts/GroupedBarChart.tsx`、`src/components/ui/charts/MultiLineChart.tsx`、
`src/features/optimization/components/{BenchmarkTable,BenchmarkComparisonChart,InputSizeCurveChart,BenchmarkPanel}.tsx`、
`src/app/(pages)/optimization/benchmark/page.tsx`。
**既存ファイルへの変更**: `src/lib/menu-tree.ts`(`Optimization` グループを追加。現行版は samples)。

対応サンプル: `samples/ui/src/components/ui/charts/{GroupedBarChart,MultiLineChart}.tsx`、
`samples/ui/src/features/optimization/components/*.tsx`、
`samples/ui/src/app/(pages)/optimization/benchmark/page.tsx`、`samples/ui/src/lib/menu-tree.ts`。
テストは `samples/ui/src/components/ui/charts/GroupedBarChart.test.tsx`。

---

## 1. 汎用チャート(`src/components/ui/charts/`)

既存の `BarChart` / `LineChart` は「装飾的なスパークライン」で、軸・目盛り・凡例・対数軸・
多系列が無い。ベンチマークにはそれが要る ── **既存パターン(素の `<svg>` + `theme-gradients.ts`
の配色 + `useHasMounted` でハイドレーション対策)を踏襲**して 2 つ足す。**名前はドメイン非依存**
(`GroupedBarChart` / `MultiLineChart`)── DeciTima 固有語を汎用層に入れない
(ルート CLAUDE.md「還元を見越したネーミング」)。将来 `next-tamagui-templates` へ戻す候補。

### 1.1 `GroupedBarChart`

```typescript
export type BarSeries = { label: string; values: number[] };
export function GroupedBarChart({ groups, series, width, height, yTicks, valueFormat }: {...}) { ... }
```

- `groups`(x 軸ラベル)× `series`(グループ内の複数棒)。`series[i].values[j]` が group j の
  系列 i の値。
- y 軸: `max` を `yTicks` 等分した目盛り線 + ラベル。棒は各グループ内で系列ぶん横並び。
- 配色は `useChartPalette(mounted ? resolvedTheme : undefined)` ── ハイドレーション直後は
  light 既定に固定して flash を防ぐ(`PieChart.tsx` と同じ)。

### 1.2 `MultiLineChart`

```typescript
export type LineSeries = { label: string; points: number[] };
export function MultiLineChart({ xLabels, series, logScale, yTicks, valueFormat }: {...}) { ... }
```

- **`logScale` オプション**が肝 ── 全探索が指数的に伸びるので、線形軸だと Dijkstra の線が
  底に張り付いて見えない。`logScale` で `Math.log10` スケールに切り替え、目盛りも
  `10 ** (lo + step*i)` で刻む。
- `xLabels` は points のインデックスに対応(= 問題サイズ)。

> **`@tamagui/next-theme` とテスト**: `useThemeSetting` は `NextThemeProvider` 経由で
> `next/script` を読むため jsdom で解決できない。チャートのテストでは
> `vi.mock("@tamagui/next-theme", () => ({ useThemeSetting: () => ({ resolvedTheme: "light" }) }))`
> で最小モックする(このリポジトリで `@tamagui/next-theme` を使うコンポーネントの初テスト)。

---

## 2. feature コンポーネント(`src/features/optimization/components/`)

| コンポーネント | 役割 |
| --- | --- |
| `BenchmarkTable` | Algorithm × 6 指標の表(README §14 の出力形)。既存の Tamagui プリミティブで組む |
| `BenchmarkComparisonChart` | `GroupedBarChart` に「実行時間 / 操作回数 / メモリ」を渡す。3 指標は単位が違うので**各指標の最大値 = 1 に正規化**(絶対値はテーブルで見る) |
| `InputSizeCurveChart` | `MultiLineChart`(`logScale`)に「サイズ vs アルゴリズム別 `_ops`」を渡す。データはサイズを振って `runBenchmark` を複数回叩いて用意 |
| `BenchmarkPanel` | `"use client"`。デモ問題を選んで実行 → テーブル + グループ棒を表示。`useBenchmark` を使う |

```typescript
// BenchmarkPanel.tsx(要点)
export function BenchmarkPanel() {
  const { result, status, error, run } = useBenchmark();
  return (
    <YStack gap="$4" padding="$4">
      {/* 操作回数はアルゴリズム定義の単位、という注記 */}
      <Button disabled={status === "loading"}
        onPress={() => void run({ problem: SAMPLE_ROUTE_PROBLEM, runs: 5 })}>
        {status === "loading" ? <Spinner /> : "デモ問題でベンチマークを実行"}
      </Button>
      {result ? <><BenchmarkTable entries={result.entries} />
                   <BenchmarkComparisonChart entries={result.entries} /></> : null}
    </YStack>
  );
}
```

---

## 3. ページと MENU_TREE

```typescript
// src/app/(pages)/optimization/benchmark/page.tsx
import { RequireAuth } from "@/components/auth/RequireAuth";
import { BenchmarkPanel } from "@/features/optimization/components/BenchmarkPanel";

export default function BenchmarkPage() {
  return (
    <RequireAuth>
      <BenchmarkPanel />
    </RequireAuth>
  );
}
```

- **SSG のまま** ── ページはただ `BenchmarkPanel`(client)を置くだけ。バックエンドへの
  問い合わせは `BenchmarkPanel` 内の `apiFetch` で**クライアント側**で行う
  (`decitima-ui/CLAUDE.md`「全ページ SSG が基本」)。
- **`<RequireAuth>` で包む**(3-5 で用意した認証基盤の消費者)── `POST /api/v1/benchmark` は
  認証必須(`Phase-0-7.md` §6.1)。未ログインだと `LoginRequiredDialog` が出て
  `/login?redirect=/optimization/benchmark` へ誘導する(生の 401 を見せない)。
- `(pages)/(sample)/` ではなく `(pages)/optimization/` ── デモではなく DeciTima の機能画面。

```typescript
// src/lib/menu-tree.ts に追加
  {
    label: "Optimization",
    children: [{ label: "アルゴリズム比較(Benchmark)", href: "/optimization/benchmark" }],
  },
```

新しいページを足したら `MENU_TREE` にも追記(サイドメニュー・トップページ・404 が共有)。

---

## 4. まとめ

- 汎用の軸付きチャート 2 つを `src/components/ui/charts/` に(ドメイン非依存名、還元候補)。
- `MultiLineChart` の対数軸オプションが「全探索は指数的に爆発」を 1 枚で見せる鍵。
- ページは SSG、データ取得はクライアント側の `apiFetch`。

## テスト観点(`samples/ui/src/components/ui/charts/GroupedBarChart.test.tsx`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `GroupedBarChart`(描画)
> - **ドライバ**: `@testing-library/react` の `render`。`TamaguiProvider` でラップ
> - **スタブ**: `vi.mock("@tamagui/next-theme")` ── jsdom で解決できない `next/script` 依存を
>   避けるための最小モック。`resolvedTheme` 文字列しか要らない

| ケース | 期待 |
| --- | --- |
| 2 グループ × 2 系列 | `<rect>` が 4 本 / 系列ぶんの凡例(「実行時間」「操作回数」) |
| x 軸ラベル | グループ名(`dijkstra` / `brute_force`)が描画される |

`npx vitest run src/components/ui/charts src/features/optimization` / `npx tsc --noEmit` /
`npm run lint`。

---

## 5. 次章

benchmark 機能（backend + UI）はこれで一通り動く。次章([Phase-3-8](./Phase-3-8.md))は
作業単位 3-8 ── `benchmark_runs` に貯まった実測を pandas で集計・可視化する分析トラック
`analysis/`（decitima-api。`app/` から切り離したオフライントラック。Phase 4 以降が育てる器）。
UI（3-6/3-7）とは独立なので、benchmark を使う人が余裕のあるときに写経すればよい。
