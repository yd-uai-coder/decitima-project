// DeciTima samples │ 作業単位 15-8
import { test, expect } from "@playwright/test";

/**
 * README §15「E2E」の代表シナリオ①(直接入力パターン)。
 * ログイン → Route Planner でサンプル問題を選択 → 「解く(自動選択)」→ 経路の可視化を確認。
 * 他5ドメイン(network/shift/project/logistics + benchmark)は同じ「サンプル選択→解く」
 * パターンなので省略する(Phase-15-8.md §非スコープ)。
 *
 * 実行には `example-user@example.com` / `sample-user-0123`(`scripts/seed.py`)が
 * 投入済みのバックエンドが必要(`NEXT_PUBLIC_API_URL` で向き先を指定)。
 */
test("login -> route planner -> solve", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill("example-user@example.com");
  await page.getByLabel("パスワード").fill("sample-user-0123");
  await page.getByRole("button", { name: "ログイン" }).click();
  // router.replace は非同期(loginRequest → login() → replace)なので、/login を
  // 抜けるまで待ってから次のページへ遷移する(先に goto すると未ログイン扱いで弾かれる)
  await page.waitForURL((url) => !url.pathname.startsWith("/login"));

  await page.goto("/optimization/route-planner");
  await page.getByRole("button", { name: "基本(A→E、期待最短 5)" }).click();
  await page.getByRole("button", { name: "解く(自動選択)" }).click();

  await expect(page.getByText(/経路\(/)).toBeVisible({ timeout: 15000 });
});
