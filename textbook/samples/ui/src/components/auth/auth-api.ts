// DeciTima samples │ Phase 3
import { apiFetch } from "@/lib/api/client";
import type { TokenPair } from "@/lib/api/types";

/**
 * POST /api/v1/auth/login ── メール + パスワードでトークンペアを得る。
 *
 * auth-store は「トークンを保存するだけ」で API 呼び出しは持たない設計(エンドポイントの形は
 * アプリごとに違うため)。その DeciTima 側の実装がこの 1 関数。得たトークンは呼び出し側で
 * useAuthStore.getState().login(access, refresh) に渡す。
 * 資格情報が誤っていれば apiFetch が 401 の ApiError を投げる(未ログイン状態なので
 * サイレントリフレッシュは走らない)。
 */
export function loginRequest(email: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
