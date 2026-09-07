import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import { TamaguiProvider } from "tamagui";
import tamaguiConfig from "../../../../tamagui.config";

vi.mock("@tamagui/next-theme", () => ({
  useThemeSetting: () => ({ resolvedTheme: "light" }),
}));

import { GraphCanvas } from "./GraphCanvas";

const NODES = [{ id: "A" }, { id: "B" }, { id: "C" }];
const EDGES = [
  { id: "e_ab", source: "A", target: "B", weight: 2 },
  { id: "e_bc", source: "B", target: "C", weight: 3, directed: true },
];

function renderCanvas(props: Partial<Parameters<typeof GraphCanvas>[0]> = {}) {
  return render(
    <TamaguiProvider config={tamaguiConfig} defaultTheme="light">
      <GraphCanvas nodes={NODES} edges={EDGES} {...props} />
    </TamaguiProvider>,
  );
}

describe("GraphCanvas", () => {
  it("draws one <circle> per node and one <line> per edge", () => {
    const { container } = renderCanvas();
    expect(container.querySelectorAll("circle")).toHaveLength(3);
    expect(container.querySelectorAll("line")).toHaveLength(2);
  });

  it("adds an arrowhead marker only to directed edges", () => {
    const { container } = renderCanvas();
    const marked = [...container.querySelectorAll("line")].filter((l) => l.getAttribute("marker-end"));
    expect(marked).toHaveLength(1);
  });

  it("dashes candidate edges passed via dashedEdgeIds", () => {
    const { container } = renderCanvas({ dashedEdgeIds: ["e_ab"] });
    const dashed = [...container.querySelectorAll("line")].filter((l) => l.getAttribute("stroke-dasharray"));
    expect(dashed).toHaveLength(1);
  });
});
