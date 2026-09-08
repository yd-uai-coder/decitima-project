// DeciTima samples │ Phase 3
import { Suspense } from "react";
import { LoginForm } from "@/components/auth/LoginForm";

// SSG のまま。LoginForm は useSearchParams(?redirect=) を読むので Suspense 境界が要る
// (Next.js の要件 ── これが無いとビルドが CSR bailout エラーになる)。
export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
