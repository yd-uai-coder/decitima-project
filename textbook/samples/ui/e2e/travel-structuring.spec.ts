// DeciTima samples │ 作業単位 15-9
import { test, expect } from "@playwright/test";

/**
 * README §15「E2E」の代表シナリオ②(LLM構造化パターン)。
 * ログイン → 自然言語入力 →「内容を理解する」→ 確認カード →「この条件で最適化する」→
 * Travel Planner へ遷移 →「プランを作る(Knapsack DP)」→ 結果の可視化を確認。
 *
 * バックエンドは `E2E_TESTING=true` で起動すること(実 Gemini API を呼ばず、
 * `app/ai/llm/e2e_fixture.py` の固定応答を返す ── 詳細 `Phase-15-9.md`)。
 * それ以外の設定(seed 済みユーザー等)は route-planner.spec.ts と同じ。
 */
test("login -> structuring -> confirm -> travel planner -> solve", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill("example-user@example.com");
  await page.getByLabel("パスワード").fill("sample-user-0123");
  await page.getByRole("button", { name: "ログイン" }).click();
  await page.waitForURL((url) => !url.pathname.startsWith("/login"));

  await page.goto("/optimization/structuring");
  await page.getByLabel("natural-language-input").fill("5万円以内で東京を2日間旅行したい。");
  await page.getByRole("button", { name: "内容を理解する" }).click();

  await expect(page.getByText("AIが理解した条件")).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "この条件で最適化する" }).click();

  await page.waitForURL(/\/optimization\/travel-planner/);
  await page.getByRole("button", { name: "プランを作る(Knapsack DP)" }).click();

  await expect(page.getByText(/旅行プラン\(/)).toBeVisible({ timeout: 15000 });
});
