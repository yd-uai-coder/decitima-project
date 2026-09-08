// DeciTima samples │ Phase 3
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { TamaguiProvider } from "tamagui";
import tamaguiConfig from "../../../../tamagui.config";

// @tamagui/next-theme は NextThemeProvider 経由で next/script を読むため jsdom で解決できない。
// チャートは resolvedTheme 文字列しか要らないので最小モックで足りる。
vi.mock("@tamagui/next-theme", () => ({
  useThemeSetting: () => ({ resolvedTheme: "light" }),
}));

import { GroupedBarChart } from "./GroupedBarChart";

function renderChart() {
  return render(
    <TamaguiProvider config={tamaguiConfig} defaultTheme="light">
      <GroupedBarChart
        groups={["dijkstra", "brute_force"]}
        series={[
          { label: "実行時間", values: [0.2, 0.8] },
          { label: "操作回数", values: [0.1, 1.0] },
        ]}
      />
    </TamaguiProvider>,
  );
}

describe("GroupedBarChart", () => {
  it("renders one <rect> per (group, series) pair and a legend entry per series", () => {
    const { container } = renderChart();
    // 2 グループ × 2 系列 = 4 本
    expect(container.querySelectorAll("rect")).toHaveLength(4);
    expect(screen.getByText("実行時間")).toBeInTheDocument();
    expect(screen.getByText("操作回数")).toBeInTheDocument();
  });

  it("renders the group labels on the x axis", () => {
    renderChart();
    expect(screen.getByText("dijkstra")).toBeInTheDocument();
    expect(screen.getByText("brute_force")).toBeInTheDocument();
  });
});
