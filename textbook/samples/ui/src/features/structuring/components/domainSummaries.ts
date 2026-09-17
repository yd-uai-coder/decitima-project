// DeciTima samples │ Phase 11(11-8)
import type { OptimizationProblem } from "@/lib/api/types";

export type SummaryItem = { label: string; value: string };

/**
 * problem_type → 確認カードに表示する要約項目(README §11 モックの「予算/期間/必須訪問先/
 * 優先事項/最小化目的」に相当)。backend の `EXTRACTORS`(app/services/structuring.py)と
 * 対の設計 ── 「どのドメインでどのフィールドを人間に見せるか」を1箇所に集約する。
 */
export function summarize(problem: OptimizationProblem): SummaryItem[] {
  const items: SummaryItem[] = [
    {
      label: "目的",
      value:
        problem.objectives
          .map((o) => `${o.sense === "minimize" ? "最小化" : "最大化"}: ${o.target}`)
          .join(", ") || "(抽出できませんでした)",
    },
  ];
  if (problem.constraints && problem.constraints.length > 0) {
    items.push({ label: "制約", value: `${problem.constraints.length} 件` });
  }

  switch (problem.data.problem_type) {
    case "travel_planning":
      items.push({ label: "予算", value: `¥${problem.data.budget.toLocaleString()}` });
      items.push({ label: "使える時間", value: `${problem.data.time_budget}` });
      if (problem.data.start) items.push({ label: "起点", value: problem.data.start });
      break;
    case "route_planning":
      items.push({ label: "出発", value: problem.data.start });
      items.push({ label: "到着", value: problem.data.goal });
      break;
    case "shift_scheduling":
      items.push({
        label: "週あたり上限時間",
        value: `${problem.data.max_weekly_hours ?? "-"}`,
      });
      break;
    case "project_scheduling":
      items.push({
        label: "資源上限",
        value: problem.data.resource_capacity != null ? `${problem.data.resource_capacity}` : "制約なし",
      });
      break;
    case "logistics_planning":
      items.push({ label: "デポ", value: problem.data.depot_id });
      break;
    case "network_design":
      break; // トップレベル・スカラーを持たないため追加項目なし(11-5 の EXTRACTORS と対応)
  }
  return items;
}

/** 確定後の遷移先(README §11「Optimization」への遷移)。既存の各ドメインページを再利用する。 */
export const PROBLEM_TYPE_ROUTES: Record<OptimizationProblem["problem_type"], string> = {
  route_planning: "/optimization/route-planner",
  network_design: "/optimization/network-designer",
  shift_scheduling: "/optimization/shift-scheduler",
  travel_planning: "/optimization/travel-planner",
  project_scheduling: "/optimization/project-planner",
  logistics_planning: "/optimization/logistics-planner",
};
