// DeciTima samples │ Phase 11
// @vitest-environment node
import { describe, expect, it } from "vitest";
import type { OptimizationProblem } from "@/lib/api/types";
import { PROBLEM_TYPE_ROUTES, summarize } from "./domainSummaries";

const TRAVEL_PROBLEM: OptimizationProblem = {
  problem_type: "travel_planning",
  objectives: [{ sense: "maximize", target: "total_value" }],
  constraints: [{ kind: "required_inclusion", items: ["P1"] }],
  data: {
    problem_type: "travel_planning",
    places: [],
    legs: [],
    budget: 50000,
    time_budget: 16,
    start: "P0",
  },
};

describe("summarize", () => {
  it("includes objectives and travel-specific fields", () => {
    const items = summarize(TRAVEL_PROBLEM);
    expect(items).toContainEqual({ label: "目的", value: "最大化: total_value" });
    expect(items).toContainEqual({ label: "予算", value: "¥50,000" });
    expect(items).toContainEqual({ label: "起点", value: "P0" });
    expect(items).toContainEqual({ label: "制約", value: "1 件" });
  });

  it("shows a fallback message when no objectives were extracted", () => {
    const items = summarize({ ...TRAVEL_PROBLEM, objectives: [] });
    expect(items[0]).toEqual({ label: "目的", value: "(抽出できませんでした)" });
  });

  it("omits the 制約 row when there are no constraints", () => {
    const items = summarize({ ...TRAVEL_PROBLEM, constraints: [] });
    expect(items.some((item) => item.label === "制約")).toBe(false);
  });
});

describe("PROBLEM_TYPE_ROUTES", () => {
  it("covers all six problem types", () => {
    expect(Object.keys(PROBLEM_TYPE_ROUTES).sort()).toEqual(
      [
        "route_planning",
        "network_design",
        "shift_scheduling",
        "travel_planning",
        "project_scheduling",
        "logistics_planning",
      ].sort()
    );
  });
});
