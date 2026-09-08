// DeciTima samples │ Phase 4
import { RequireAuth } from "@/components/auth/RequireAuth";
import { RoutePlannerPanel } from "@/features/optimization/route-planner/components/RoutePlannerPanel";

// SSG のまま ── backend への問い合わせは RoutePlannerPanel(client)側。
// solve / benchmark は認証必須なので RequireAuth で包む(Phase 3-5 の認証基盤の消費者)。
export default function RoutePlannerPage() {
  return (
    <RequireAuth>
      <RoutePlannerPanel />
    </RequireAuth>
  );
}
