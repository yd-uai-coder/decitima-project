// DeciTima samples │ Phase 8
import { RequireAuth } from "@/components/auth/RequireAuth";
import { ProjectPlannerPanel } from "@/features/optimization/project-planner/components/ProjectPlannerPanel";

// SSG のまま。solve / benchmark は認証必須なので RequireAuth で包む。
export default function ProjectPlannerPage() {
  return (
    <RequireAuth>
      <ProjectPlannerPanel />
    </RequireAuth>
  );
}
