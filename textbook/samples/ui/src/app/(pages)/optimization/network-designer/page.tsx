// DeciTima samples │ Phase 5
import { RequireAuth } from "@/components/auth/RequireAuth";
import { NetworkDesignerPanel } from "@/features/optimization/network-designer/components/NetworkDesignerPanel";

// SSG のまま。solve / benchmark は認証必須なので RequireAuth で包む。
export default function NetworkDesignerPage() {
  return (
    <RequireAuth>
      <NetworkDesignerPanel />
    </RequireAuth>
  );
}
