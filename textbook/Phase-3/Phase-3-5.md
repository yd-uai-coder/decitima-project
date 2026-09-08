# Phase 3-5: 最小ログイン UI(`/login` + `RequireAuth` 配線)(作業単位 3-5)

## この章のゴール

主に decitima-ui の作業。**ログインフォームを 1 枚作り、テストユーザーをシードする。**

- `POST /api/v1/auth/login` を叩く 1 関数 `loginRequest`
- メール + パスワードの `LoginForm`(`useState` だけの最小構成)
- `/login` ページ(`?redirect=` を読んで元の画面へ戻す)
- テンプレの `refreshTokens()` を DeciTima backend の `/auth/refresh` 契約に合わせて修正
- decitima-api に `scripts/seed.py` ── `/login` で使う固定テストユーザーを 1 コマンドで登録（§8）
- （benchmark ページを `<RequireAuth>` で包むのは 3-7。この章はその配線先の認証基盤を用意する）

**この章で作成 / 更新するファイル**:
- decitima-ui: `src/components/auth/auth-api.ts`、`src/components/auth/LoginForm.tsx`、
  `src/app/(pages)/login/page.tsx`。テスト: `src/components/auth/auth-api.test.ts`、
  `src/components/auth/LoginForm.test.tsx`。
- decitima-api: `scripts/__init__.py`、`scripts/seed.py`（テストユーザーのシード。§8）。

**既存ファイルへの変更**（現行版は samples）:
`src/components/auth/auth-store.ts`(`refreshTokens()` の修正)、
`src/lib/api/types.ts`(`TokenPair` / `AccessToken` を追記 ── benchmark DTO は 3-6)。

対応サンプル: `textbook/samples/ui/src/components/auth/{auth-api.ts,LoginForm.tsx}`、
`textbook/samples/ui/src/app/(pages)/login/page.tsx`、`textbook/samples/ui/src/components/auth/auth-store.ts`、
`textbook/samples/ui/src/lib/api/types.ts`、`textbook/samples/scripts/{__init__,seed}.py`。
設計は `Phase-0-7.md` §6.1（認証必須）、`decitima-ui/CLAUDE.md`「バックエンド連携」。

> **`node_modules/next/dist/docs/` の該当ガイドを先に読む**（`decitima-ui/AGENTS.md`）──
> ページ / クライアントコンポーネントを書く前に `01-app/01-getting-started` を確認。

---

## 1. なぜログインを 3-5(feature の前)に置くか

- benchmark のページ章（3-7）は**ブラウザで実 backend に繋いで動作確認する初の UI**。その前提が
  「ログイン済みであること」── `POST /api/v1/benchmark` は `current_user: CurrentUserDep` を
  **ハンドラ本体より前に**解決し、Bearer トークンが無ければ即 `401 "Could not validate credentials"`
  を返す（`app/api/deps.py`。`benchmark_runs` を user_id でスコープするための設計。`Phase-0-7.md` §6.1）。
- api 層 / stores / hooks（3-6）は `vi.mock` で `apiFetch` を潰すので認証不要だが、その先で必ず要る。
- backend の認証（JWT: `/api/v1/auth/{register,login,refresh}`）と UI の認証ストア
  （`auth-store.ts` + `RequireAuth` / `LoginRequiredDialog`）は**テンプレートで実装済み**。
  不足しているのは「実トークンを取得してストアに入れる導線 = ログインフォーム」だけ。
- `LoginForm` は `src/components/auth/`（app-shell の部品。`src/features/` より**下の層**）。
  **下の層から積む**という依存方向にも合う。

### 範囲外（この章では作らない）

登録画面 / パスワードリセット / Remember me / ソーシャルログイン / エラーの細かい分類 /
ログイン状態のヘッダー表示。必要になった Phase で足す。

---

## 2. `src/lib/api/types.ts` ── 認証 DTO(既存ファイルへの追記)

```typescript
// backend の app/schemas/auth.py と対応
export type TokenPair = { access_token: string; refresh_token: string };
export type AccessToken = { access_token: string };
```

- `POST /auth/login` は `TokenPair`（access + refresh）を返す。
- `POST /auth/refresh` は **`AccessToken`（access だけ）** を返す ── DeciTima backend は
  リフレッシュトークンを**ローテーションしない**（§4 で効いてくる）。
- samples の `types.ts` は 3-6 の benchmark DTO も含む現行版。3-5 時点では auth 型だけ使う。

---

## 3. `src/components/auth/auth-api.ts` ── login の 1 関数

```typescript
// src/components/auth/auth-api.ts
export function loginRequest(email: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
```

- `auth-store` は「トークンを保存するだけ」で API 呼び出しを持たない設計（エンドポイントの形は
  アプリごとに違うため。`decitima-ui/CLAUDE.md`）。その DeciTima 側の実装がこの 1 関数。
- 資格情報が誤っていれば `apiFetch` が **401 の `ApiError`** を投げる。未ログイン状態なので
  `apiFetch` のサイレントリフレッシュ分岐（`401 && accessToken`）はスキップされ、そのまま throw。

---

## 4. `src/components/auth/auth-store.ts` ── `refreshTokens()` の修正

テンプレートの `refreshTokens()` は `/auth/refresh` から `TokenPair` を期待し
`refreshToken: tokens.refresh_token` を set していた。DeciTima backend は `AccessToken`
（access だけ）を返すので、この `refresh_token` は `undefined` になり、次のリフレッシュで
`refreshToken` を失って壊れる。

```typescript
// 修正後(要点)
const token = await apiFetch<AccessToken>("/api/v1/auth/refresh", {
  method: "POST",
  body: JSON.stringify({ refresh_token: currentRefreshToken }),
});
useAuthStore.setState({ accessToken: token.access_token });   // refreshToken は据え置き
scheduleSilentRefresh(token.access_token);
```

- `login` / `logout` / `scheduleSilentRefresh` / `decodeJwtExpMs` は変更なし。
- ローカルの `type TokenPair = ...` は削除し `@/lib/api/types` から import（1 箇所に集約）。
- これはテンプレート由来のバグ。`next-tamagui-templates` ↔ `fastapi-langchain-template` の
  `/auth/refresh` レスポンス契約の不整合として**テンプレートへ還元候補**。

---

## 5. `src/components/auth/LoginForm.tsx`

`"use client"`。`useState` で `email` / `password` / `error` / `submitting` を持つだけ。

| 分岐 | 表示 / 動作 |
| --- | --- |
| `!mounted`（localStorage 復元前） | `null`（ハイドレーション不一致回避。`useHasMounted`） |
| `accessToken` あり（既ログイン） | 「ログイン中です」+ ログアウトボタン |
| それ以外 | メール / パスワード + 「ログイン」ボタン |

送信:

```
loginRequest(email, password)
  → useAuthStore.getState().login(access_token, refresh_token)
  → router.replace(redirect ?? "/optimization/benchmark")
catch: ApiError なら err.message、それ以外は「ログインに失敗しました」を <Paragraph role="alert"> に
```

- `redirect` は `useSearchParams().get("redirect")`（`RequireAuth` → `LoginRequiredDialog` が
  `?redirect=<元パス>` を付ける）。
- 入力は tamagui の `Input` + `@/components/ui/primitives/StyledButton` を直接使う
  （`InputEmail` / `InputPassword` は react-hook-form バウンドで、この最小フォームには重い）。
- `<form onSubmit>` は素の HTML 要素。tamagui の `YStack` はレイアウトだけ。二重送信は
  `submitting` ガード。

---

## 6. `src/app/(pages)/login/page.tsx`

```typescript
export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
```

- **`<Suspense>` 必須** ── `LoginForm` が `useSearchParams()` を読むため。無いと Next の
  ビルドが「CSR bailout」エラーになる（`node_modules/next/dist/docs/` のガイド参照）。
- SSG のまま（ページは静的、フォームはクライアントで動く）。
- `(pages)/(sample)/` ではなく `(pages)/login/` ── デモではなくアプリの画面。
- `MENU_TREE` には**足さない**（ログインはメニュー項目でなく、ガードからの誘導先）。

---

## 7. この章の消費者 ── benchmark ページ（3-7 で作る）

benchmark ページ（`src/app/(pages)/optimization/benchmark/page.tsx`）は 3-7 で新規作成するが、
その時点で `<RequireAuth>` で包む ── この章で用意した認証基盤の消費者になる:

```typescript
// 3-7 で作る page.tsx(先取り)
export default function BenchmarkPage() {
  return (
    <RequireAuth>
      <BenchmarkPanel />
    </RequireAuth>
  );
}
```

- 未ログインだと `RequireAuth`（既存）が `LoginRequiredDialog` を出し、
  `/login?redirect=/optimization/benchmark` へ誘導する（生の 401 エラーを見せない）。
- `RequireAuth` は `"use client"`。ページは server component のまま、その配下が client。SSG 維持。
- この章だけを写経した時点では `/login` を直接開いて（`http://localhost:3000/login`）
  ログイン → `/optimization/benchmark` に手で移動して 401 が消えることを確認できる。

---

## 8. 動作確認 ── テストユーザーのシード（backend への追記）

ログインするには **DB にユーザーが 1 人要る**。`/docs` の `POST /api/v1/auth/register` を手で
叩いてもよいが、固定のテストユーザーを 1 コマンドで作れるシードスクリプトを置く。

```python
# decitima-api/backend/scripts/seed.py（要点。全文は samples）
SEED_USER = {
    "full_name": "sample-user",
    "email": "example-user@example.com",
    "password": "sample-user-0123",
}

async def seed() -> None:
    async with AsyncSessionLocal() as session:
        try:
            user = await UserService(session).create_user(
                email=SEED_USER["email"],
                password=SEED_USER["password"],
                full_name=SEED_USER["full_name"],
            )
            print(f"created user: {user.email} ({user.id})")
        except UserAlreadyExistsError:
            print(f"user already exists: {SEED_USER['email']} (skip)")
```

- **置き場は `scripts/`**（`analysis/` / `tests/` と同じ「`app/` の上」。`app/` から import されない。
  `scripts/__init__.py` を置き `python -m scripts.seed` で実行）。
- `UserService.create_user`（`app/services/user.py`）が **重複チェック + パスワードハッシュ +
  `commit`** をすべて持つので、スクリプト側は薄い。`UserAlreadyExistsError` を握って**冪等**に。
- **dev 専用**。本番 DB では実行しない。

```bash
# ローカル
cd decitima-api/backend
uv run alembic upgrade head           # users テーブルが要る
uv run python -m scripts.seed

# docker
docker compose run --rm backend uv run alembic upgrade head
docker compose run --rm backend uv run python -m scripts.seed
```

そのあと `http://localhost:3000/login` で
`example-user@example.com` / `sample-user-0123` を入力 → benchmark 画面（3-7 完成後）で「実行」が
200 を返す。

---

## 9. テスト観点

> **テスト対象 / ドライバ / スタブ**（進行のルール #14。用語は `Phase-1-1.md` §テスト観点で定義済み）:
> - `auth-api.test.ts`（node env）: **対象** = `loginRequest`。**ドライバ** = テスト関数。
>   **スタブ** = `vi.mock("@/lib/api/client")` で `apiFetch` を差し替え、呼ばれたパス・method・body を検証。
> - `LoginForm.test.tsx`（jsdom）: **対象** = `LoginForm`（描画 + 送信フロー）。**ドライバ** =
>   `@testing-library/react` の `render` + `@testing-library/user-event`。
>   **スタブ** = `vi.mock("./auth-api")`（`loginRequest`）+ `vi.mock("next/navigation")`（`useRouter`
>   の `replace` / `useSearchParams`）。`useAuthStore` は**本物**（`setState` で初期状態を作る。
>   zustand persist は jsdom の localStorage で動く ── これはスタブでなく「実物の代役が要らない」ケース）。

| ファイル | ケース | 期待 |
| --- | --- | --- |
| auth-api | `loginRequest("u@e.c", "pw")` | `POST /api/v1/auth/login` / body `{email, password}` / `TokenPair` を返す |
| auth-api | `apiFetch` が reject | そのまま throw（401 を握り潰さない） |
| LoginForm | 正しい資格情報で送信 | `login(access, refresh)` がストアに反映 / `router.replace("/optimization/benchmark")` |
| LoginForm | `ApiError(401)` | `role="alert"` に "Could not validate credentials" / `replace` は呼ばれない / トークンは null のまま |
| LoginForm | 既に `accessToken` あり | 「ログイン中です」表示 / メール入力は出ない |

`npx vitest run src/components/auth` / `npx tsc --noEmit` /
`npx eslint src/components/auth 'src/app/(pages)/login/page.tsx'`。

`scripts/seed.py` は薄い一発スクリプトなのでテストは書かない（`UserService` 側にテストがある）。
overlay 検証で `alembic upgrade head` → `python -m scripts.seed` を 2 回流し「作成 → skip」を確認する。

---

## 10. 次章

これで benchmark 画面を実ログインで開けるようになった。次章
([Phase-3-6](./Phase-3-6.md))から作業単位 3-6 ── 初の `src/features/optimization/`
（可視化ライブラリの選定 + api 層 / stores / hooks）。
