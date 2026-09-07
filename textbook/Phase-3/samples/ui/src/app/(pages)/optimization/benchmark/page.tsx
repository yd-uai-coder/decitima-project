import { RequireAuth } from "@/components/auth/RequireAuth";
import { BenchmarkPanel } from "@/features/optimization/components/BenchmarkPanel";

// SSG(静的生成)のまま ── バックエンドへの問い合わせは BenchmarkPanel(client)側で行う。
// benchmark は認証必須(Phase-0-7 §6.1)なので RequireAuth で包む。未ログインなら
// LoginRequiredDialog が出て /login?redirect=/optimization/benchmark へ誘導する。
export default function BenchmarkPage() {
  return (
    <RequireAuth>
      <BenchmarkPanel />
    </RequireAuth>
  );
}
