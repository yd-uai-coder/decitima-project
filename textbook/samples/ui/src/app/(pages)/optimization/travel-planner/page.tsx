// DeciTima samples │ Phase 7
import { RequireAuth } from "@/components/auth/RequireAuth";
import { TravelPlannerPanel } from "@/features/optimization/travel-planner/components/TravelPlannerPanel";

// SSG のまま。solve / benchmark は認証必須なので RequireAuth で包む。
export default function TravelPlannerPage() {
  return (
    <RequireAuth>
      <TravelPlannerPanel />
    </RequireAuth>
  );
}
