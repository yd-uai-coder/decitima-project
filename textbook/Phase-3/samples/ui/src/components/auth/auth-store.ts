import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiFetch } from "@/lib/api/client";
import type { AccessToken, AsyncStatus } from "@/lib/api/types";

type AuthStore = {
  accessToken: string | null;
  refreshToken: string | null;
  status: AsyncStatus;
  error: string | null;
  // 実際のログインAPI呼び出し(エンドポイントの形はアプリごとに異なるため)は呼び出し側で行い、
  // 得られたトークンをこの関数へ渡してストアへ保存する(DeciTima では auth-api.loginRequest)。
  login: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
};

// アクセストークンの有効期限切れの何秒前にサイレントリフレッシュを走らせるか
const SILENT_REFRESH_MARGIN_SECONDS = 60;

// リロード後もログイン状態を維持するため、トークンのみlocalStorageへ永続化する
// (status/errorは一時的なUI状態のため保存しない)。
export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      status: "idle",
      error: null,
      login: (accessToken, refreshToken) => {
        set({ accessToken, refreshToken, status: "success", error: null });
        scheduleSilentRefresh(accessToken);
      },
      // トークンを破棄しログアウト状態に戻す。サーバー側のリフレッシュトークン失効APIが
      // あれば、必要に応じてここでベストエフォート(失敗を無視)で呼び出す。
      logout: () => {
        scheduleSilentRefresh(null);
        set({ accessToken: null, refreshToken: null, status: "idle", error: null });
      },
    }),
    {
      name: "auth",
      partialize: (state) => ({ accessToken: state.accessToken, refreshToken: state.refreshToken }),
      // ページ読み込み直後、localStorageから復元したトークンに対してもサイレントリフレッシュの
      // タイマーを仕掛け直す(ログイン直後の場合はlogin()側で既にスケジュール済み)。
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken) scheduleSilentRefresh(state.accessToken);
      },
    }
  )
);

let refreshTimer: ReturnType<typeof setTimeout> | null = null;
let refreshPromise: Promise<boolean> | null = null;

// JWTのexp(秒)をデコードする。署名検証はしない(有効期限の目安を読むだけの用途のため)。
function decodeJwtExpMs(token: string): number | null {
  try {
    const payload = token.split(".")[1];
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = JSON.parse(atob(normalized)) as { exp?: number };
    return typeof json.exp === "number" ? json.exp * 1000 : null;
  } catch {
    return null;
  }
}

// 次回のサイレントリフレッシュのタイマーを(再)設定する。accessTokenがnullなら解除するのみ。
function scheduleSilentRefresh(accessToken: string | null): void {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
  if (!accessToken) return;

  const expMs = decodeJwtExpMs(accessToken);
  if (expMs === null) return;

  const delay = Math.max(expMs - Date.now() - SILENT_REFRESH_MARGIN_SECONDS * 1000, 0);
  refreshTimer = setTimeout(() => {
    void refreshTokens();
  }, delay);
}

// リフレッシュトークンでアクセストークンだけを再発行する。DeciTima backend の
// POST /api/v1/auth/refresh は {refresh_token} を受け取り {access_token} のみ返す
// (リフレッシュトークンはローテーションしない ── だから refreshToken は据え置く)。
// client.ts の REFRESH_PATH と対応。多重呼び出しは 1 回にまとめる(多重リフレッシュ防止)。
export function refreshTokens(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const currentRefreshToken = useAuthStore.getState().refreshToken;
    if (!currentRefreshToken) return false;

    try {
      const token = await apiFetch<AccessToken>("/api/v1/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: currentRefreshToken }),
      });
      useAuthStore.setState({ accessToken: token.access_token });
      scheduleSilentRefresh(token.access_token);
      return true;
    } catch {
      useAuthStore.getState().logout();
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}
