// DeciTima samples │ 作業単位 15-8
import { defineConfig } from "@playwright/test";

/**
 * README §15「E2E」用の Playwright 設定。テストは `e2e/` に置く(`src/` の外 ──
 * vitest がユニット/コンポーネントテストを `src/**\/*.test.ts(x)` として colocate するのと
 * 責務を分ける)。`webServer` が `npm run dev` を自動起動するので、CI では単独コマンドで
 * 完結する(バックエンドは別途 `docker compose up` 等で用意する前提、`NEXT_PUBLIC_API_URL`
 * で向き先を切り替える)。
 */
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
