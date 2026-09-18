# Phase 15-8: Playwright セットアップ + Route Planner E2E(作業単位 15-8)

## この章のゴール

README §15「E2E Test」── `textbook/Phase-0/Phase-0-9.md` のテストピラミッド図が「E2E(Phase 15)」と予告していたものをついに実装する。Playwright を `decitima-ui` に導入し、6ドメインが共有する2つの入力パターンのうち **①直接入力パターン**(サンプル選択→JSON編集→solve)の代表として Route Planner を選ぶ(選定理由は `Phase-15-introduction.md` §7)。

**この章で作成 / 更新するファイル**: `ui/playwright.config.ts`(新規)、
`ui/e2e/route-planner.spec.ts`(新規)、`ui/package.json`(新規、`@playwright/test` +`test:e2e` スクリプト追加)。

---

## 1. なぜ Route Planner か、なぜ他5ドメインを省略するか

6ドメイン(route/network/shift/travel/project/logistics)は入力方法で見ると2種類しかない:①`ProblemJsonEditor` でサンプル選択 or JSON直接編集 → solve、②`/optimization/structuring`で自然言語入力 → 確認カード → 該当ドメインへ遷移 → solve。ドメインごとのアルゴリズムの違いは各ドメインの既存 unit/property テスト(Phase 4〜9)が既に検証済みで、E2E が再証明すべきものではない ── E2E が実演すべきは「ブラウザでこの2パターンが実際に繋がるか」そのもの。**Route Planner は①の最も早い(Phase 4)実装、Travel Planner は②の代表**(15-9)という組み合わせで、6ドメインの入力パターンを2本で代表させる。残り4ドメインは「同型のため省略」と明記する(README設計のポイント「テンプレートが既に足場を提供」と同じ思想 ── 網羅性より、本当に新しい経路だけを検証する)。

## 2. セットアップ

```json
// ui/package.json(改訂、抜粋)
"scripts": {
  ...
  "test:e2e": "playwright test"
},
"devDependencies": {
  "@playwright/test": "^1.63.0",
  ...
}
```

```typescript
// ui/playwright.config.ts(新規、全文)
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // ログイン状態をページ間で共有するシナリオのため直列実行
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
```

`e2e/` は `src/` の外に置く ── Vitest のユニット/コンポーネントテスト(`src/**/*.test.tsx`、colocate)と責務を分ける。`webServer` が `npm run dev` を自動起動するので CI では単独コマンドで完結する(バックエンドは別途起動、`NEXT_PUBLIC_API_URL` で向き先を切り替える)。

> **補足**: `NEXT_PUBLIC_API_URL` は `decitima-ui` に既にある仕組み(`.env.example` /`src/lib/api/client.ts`)で、未設定時は `http://localhost:8000` に自動フォールバックする。
> バックエンドを既定ポート(8000番、`docker compose` の既定)で起動しているだけなら、**本章のためにファイル編集や env var 指定は不要** ── `npm run dev` をそのまま起動すれば繋がる。編集が要るのは、8000番以外のポートで動かす場合や、15-9 で使う`E2E_TESTING=true` の隔離バックエンドを別ポートで同時に立てる場合だけ(`NEXT_PUBLIC_API_URL=http://localhost:XXXX npm run dev` のようにインライン指定するか、gitignore対象の `decitima-ui/.env.local` で上書きする)。`ui-ci.yml`(15-10)は`env:` ブロックで直接指定済みのため、CI側も追加編集は不要。

### 2.1 導入手順 ── インストールは2段階(写経で見落としやすい)

`package.json` に `@playwright/test` を書き足しただけでは何も入らない。**npm パッケージ本体**と
**ブラウザバイナリ**は別系統のインストールで、両方必要:

```bash
# ① npm パッケージ本体(package.json の devDependencies に @playwright/test を追記した後)
npm install

# ② ブラウザバイナリ(npmパッケージとは別。Playwrightが実際に操作するChromium本体)
npx playwright install chromium
```

①だけでは `npx playwright test` は「実行ファイルが無い」的なエラーになる、②だけではそもそも `@playwright/test` の import 自体が解決しない ── 順番は①→②(①が無いと`npx playwright` コマンド自体が動かないため)。②は初回は数十〜100MB程度のダウンロードで数分かかることがあるが、既に別プロジェクトなどで同バージョンの Chromium をインストール済みの環境なら(`~/.cache/ms-playwright` にキャッシュがあれば)再ダウンロードされず一瞬で終わる。

## 3. セレクタ選び ── `data-testid` を増やさず、既存のアクセシブルな属性で足りた

このリポジトリには `data-testid` 系の規約が無い。新しい規約を増やす前に既存コンポーネントを確認したところ、ログインフォーム(`Label htmlFor` + `Input id`)や `ProblemJsonEditor` の`TextArea`(`aria-label="problem-json"`)が既にアクセシブルな属性を持っていた ──`getByLabel`/`getByRole` だけで安定したセレクタが組める。**新しい規約(`data-testid`)を足す必要は無かった**(進行のルール #17 ── 無くても足りるものを先回りで作らない)。

```typescript
// ui/e2e/route-planner.spec.ts(新規、全文)
test("login -> route planner -> solve", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill("example-user@example.com");
  await page.getByLabel("パスワード").fill("sample-user-0123");
  await page.getByRole("button", { name: "ログイン" }).click();
  await page.waitForURL((url) => !url.pathname.startsWith("/login"));

  await page.goto("/optimization/route-planner");
  await page.getByRole("button", { name: "基本(A→E、期待最短 5)" }).click();
  await page.getByRole("button", { name: "解く(自動選択)" }).click();

  await expect(page.getByText(/経路\(/)).toBeVisible({ timeout: 15000 });
});
```

`example-user@example.com` / `sample-user-0123` は `decitima-api/backend/scripts/seed.py`が作る固定の dev ユーザー(`decitima-api/CLAUDE.md` に記載済み)。

## 4. 実測で発見した2つの落とし穴

**① ログインのナビゲーションタイミング**: `LoginForm.submit()` は
`loginRequest → login() → router.replace(redirect)` という非同期の連なりで、
ボタンクリック直後に次のページへ `page.goto()` すると `RequireAuth` にまだトークンが反映されておらず「ログインが必要です」ダイアログに弾かれる。
`page.waitForURL((url) => !url.pathname.startsWith("/login"))` で `/login` を
抜けるまで待ってから次へ進む必要がある。

**② CORS(ポート番号の一致)**: 最初 Playwright の開発サーバーをデフォルトの3000番以外
(3100番)で立てたところ、ログインが「ログインに失敗しました」で失敗した。原因は
`CORS_ORIGINS` の既定値が `["http://localhost:3000"]`(`app/core/config.py`)で、
3100番からのリクエストがブラウザ側で CORS エラーとして弾かれていたこと(バックエンドのエラーではなく、ブラウザが fetch 自体を実行させない)。`playwright.config.ts` を既定の3000番に合わせることで解消 ── **Phase 15-7 のセキュリティ監査(CORS)がここでも実際に効いていることを E2E が意図せず実演した**。

> **写経の罠**: この CORS 失敗は「バックエンドが落ちている」ように見えるエラーメッセージ(`ログインに失敗しました`、`ApiError` ではない汎用文言)を出すため原因調査が遠回りになりやすい。ブラウザの Network タブ(または Playwright の `trace: "retain-on-failure"`)で CORS エラーかどうかをまず確認する。

---

## まとめ

- Playwright を導入し、既存のアクセシブルな属性(`getByLabel`/`getByRole`)だけで
  `data-testid` を増やさずにセレクタを組めた。
- ログイン後のナビゲーションは非同期の `router.replace` を待つ必要がある。
- 開発サーバーのポート番号は `CORS_ORIGINS` の既定値(3000番)に合わせる必要がある ──Phase 15-7 の CORS 監査結果が E2E でも意味を持つことを確認した。

## テスト観点(`ui/e2e/route-planner.spec.ts`)

> **対象**: ログイン → Route Planner のブラウザ操作フロー全体
> **ドライバ**: Playwright(実ブラウザ、`npm run dev` の実サーバー)
> **スタブ不要** ── バックエンドは実際に動かす(E2E の定義上、モックしない層が無いことが目的)

| ケース                | 期待                             |
| ------------------ | ------------------------------ |
| ログイン → サンプル選択 → 解く | 「経路(...)」を含むテキストが表示される(結果の可視化) |

```bash
npm install                        # @playwright/test 本体(§2.1 ①)
npx playwright install chromium    # ブラウザバイナリ、初回のみ(§2.1 ②)
npx playwright test e2e/route-planner.spec.ts
```

**実測**: バックエンド(既存 `docker compose` dev環境)+ `npm run dev`(ポート3000)に対し
実際に実行し、1 passed(約6秒)を確認した。

---

次章([Phase-15-9](./Phase-15-9.md))では②(LLM構造化パターン)を Travel Planner で実演する。
E2E で本物の Gemini API を呼ばないための仕組みも合わせて設計する。
