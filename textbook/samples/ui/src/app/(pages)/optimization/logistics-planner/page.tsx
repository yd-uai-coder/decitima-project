// DeciTima samples │ Phase 9
import { RequireAuth } from "@/components/auth/RequireAuth";
import { LogisticsPlannerPanel } from "@/features/optimization/logistics-planner/components/LogisticsPlannerPanel";

// SSG のまま。solve / benchmark / jobs は認証必須なので RequireAuth で包む。
export default function LogisticsPlannerPage() {
  return (
    <RequireAuth>
      <LogisticsPlannerPanel />
    </RequireAuth>
  );
}
