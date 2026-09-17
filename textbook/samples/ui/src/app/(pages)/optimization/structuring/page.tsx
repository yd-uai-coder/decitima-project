// DeciTima samples │ Phase 11(11-8)
import { RequireAuth } from "@/components/auth/RequireAuth";
import { StructuringPanel } from "@/features/structuring/components/StructuringPanel";

// SSG のまま。structure は認証必須なので RequireAuth で包む。
export default function StructuringPage() {
  return (
    <RequireAuth>
      <StructuringPanel />
    </RequireAuth>
  );
}
