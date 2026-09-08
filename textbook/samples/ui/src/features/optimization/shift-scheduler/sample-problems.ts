// DeciTima samples │ Phase 6
import type { OptimizationProblem } from "@/lib/api/types";

/** Shift Scheduler のデモ問題。backend の build_shift_problem と対応(最適 labor_cost 20000)。 */
export const SHIFT_SAMPLES: { label: string; problem: OptimizationProblem }[] = [
  {
    label: "3 スタッフ × 2 日 × 2 スロット(多目的)",
    problem: {
      problem_type: "shift_scheduling",
      objectives: [
        { sense: "minimize", target: "labor_cost", weight: 0.7 },
        { sense: "maximize", target: "day_off_satisfaction", weight: 0.3 },
      ],
      constraints: [{ kind: "staffing", severity: "hard" }],
      data: {
        problem_type: "shift_scheduling",
        staff: [
          {
            id: "tanaka",
            hourly_wage: 1200,
            available_slot_ids: ["s1", "s2", "s3", "s4"],
            requested_days_off: ["2026-09-02"],
          },
          { id: "sato", hourly_wage: 1000, available_slot_ids: ["s1", "s2", "s3", "s4"] },
          { id: "ito", hourly_wage: 1100, available_slot_ids: ["s1", "s3"] },
        ],
        slots: [
          { id: "s1", day: "2026-09-01", start_hour: 9, end_hour: 14, required_headcount: 1 },
          { id: "s2", day: "2026-09-01", start_hour: 14, end_hour: 19, required_headcount: 1 },
          { id: "s3", day: "2026-09-02", start_hour: 9, end_hour: 14, required_headcount: 1 },
          { id: "s4", day: "2026-09-02", start_hour: 14, end_hour: 19, required_headcount: 1 },
        ],
        max_weekly_hours: 20,
        max_consecutive_days: 5,
      },
    },
  },
  {
    label: "勤務時間均等化つき(3 目的)",
    problem: {
      problem_type: "shift_scheduling",
      objectives: [
        { sense: "minimize", target: "labor_cost", weight: 0.7 },
        { sense: "maximize", target: "day_off_satisfaction", weight: 0.3 },
        { sense: "minimize", target: "hour_variance", weight: 100 },
      ],
      constraints: [{ kind: "staffing", severity: "hard" }],
      data: {
        problem_type: "shift_scheduling",
        staff: [
          {
            id: "tanaka",
            hourly_wage: 1200,
            available_slot_ids: ["s1", "s2", "s3", "s4"],
            requested_days_off: ["2026-09-02"],
          },
          { id: "sato", hourly_wage: 1000, available_slot_ids: ["s1", "s2", "s3", "s4"] },
          { id: "ito", hourly_wage: 1100, available_slot_ids: ["s1", "s3"] },
        ],
        slots: [
          { id: "s1", day: "2026-09-01", start_hour: 9, end_hour: 14, required_headcount: 1 },
          { id: "s2", day: "2026-09-01", start_hour: 14, end_hour: 19, required_headcount: 1 },
          { id: "s3", day: "2026-09-02", start_hour: 9, end_hour: 14, required_headcount: 1 },
          { id: "s4", day: "2026-09-02", start_hour: 14, end_hour: 19, required_headcount: 1 },
        ],
        max_weekly_hours: 20,
        max_consecutive_days: 5,
      },
    },
  },
];
