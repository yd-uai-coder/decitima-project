"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { H2, Input, Label, Paragraph, YStack } from "tamagui";
import { loginRequest } from "@/components/auth/auth-api";
import { useAuthStore } from "@/components/auth/auth-store";
import { ApiError } from "@/lib/api/client";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { useHasMounted } from "@/hooks/useHasMounted";

const DEFAULT_REDIRECT = "/optimization/benchmark";

/**
 * メール + パスワードのログインフォーム。最小構成 ── 登録画面・パスワードリセット・
 * Remember me 等は範囲外(必要になった Phase で足す)。
 *
 * 成功時: auth-api.loginRequest でトークンを取得 → useAuthStore.login() で保存 →
 * ?redirect=<path>(RequireAuth → LoginRequiredDialog が付ける)へ replace で戻る。
 * 失敗時: ApiError のメッセージ(FastAPI の 401 "Could not validate credentials" 等)を表示。
 * 既にログイン済みなら「ログイン中」+ ログアウトボタンを出す(両方向を 1 画面で扱う)。
 */
export function LoginForm() {
  const mounted = useHasMounted();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") ?? DEFAULT_REDIRECT;

  const accessToken = useAuthStore((s) => s.accessToken);
  const login = useAuthStore((s) => s.login);
  const logout = useAuthStore((s) => s.logout);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // localStorage 復元前はトークンの有無が確定しないので描画しない(ハイドレーション不一致回避)
  if (!mounted) return null;

  // 既にログイン済み
  if (accessToken) {
    return (
      <YStack gap="$3" maxWidth={420} width="100%" alignSelf="center" padding="$4">
        <H2>ログイン中です</H2>
        <StyledButton onPress={() => logout()}>ログアウト</StyledButton>
      </YStack>
    );
  }

  const submit = async () => {
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const tokens = await loginRequest(email, password);
      login(tokens.access_token, tokens.refresh_token);
      router.replace(redirect);
    } catch (err) {
      // ApiError(401 等)は detail をそのまま。それ以外は汎用文言
      setError(err instanceof ApiError ? err.message : "ログインに失敗しました");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <YStack gap="$3" maxWidth={420} width="100%" alignSelf="center" padding="$4">
        <H2>ログイン</H2>

        <Label htmlFor="login-email">メールアドレス</Label>
        <Input
          id="login-email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChangeText={setEmail}
        />

        <Label htmlFor="login-password">パスワード</Label>
        <Input
          id="login-password"
          name="password"
          secureTextEntry
          autoComplete="current-password"
          value={password}
          onChangeText={setPassword}
        />

        {error ? (
          <Paragraph role="alert" color="$red10">
            {error}
          </Paragraph>
        ) : null}

        <StyledButton onPress={() => void submit()} disabled={submitting}>
          {submitting ? "送信中…" : "ログイン"}
        </StyledButton>
      </YStack>
    </form>
  );
}
