// DeciTima samples │ Phase 10
import { RequireAuth } from "@/components/auth/RequireAuth";
import { SimulationPanel } from "@/features/optimization/simulation/components/SimulationPanel";

// SSG のまま。simulate は認証必須なので RequireAuth で包む。
export default function SimulationPage() {
  return (
    <RequireAuth>
      <SimulationPanel />
    </RequireAuth>
  );
}
