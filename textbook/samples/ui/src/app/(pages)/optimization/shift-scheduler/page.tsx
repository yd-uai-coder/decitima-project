// DeciTima samples │ Phase 6
import { RequireAuth } from "@/components/auth/RequireAuth";
import { ShiftSchedulerPanel } from "@/features/optimization/shift-scheduler/components/ShiftSchedulerPanel";

// SSG のまま。solve / benchmark は認証必須なので RequireAuth で包む。
export default function ShiftSchedulerPage() {
  return (
    <RequireAuth>
      <ShiftSchedulerPanel />
    </RequireAuth>
  );
}
