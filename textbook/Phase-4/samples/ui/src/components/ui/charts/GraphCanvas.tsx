"use client";

import { useMemo } from "react";
import { YStack } from "tamagui";
import { useThemeSetting } from "@tamagui/next-theme";
import { useHasMounted } from "@/hooks/useHasMounted";
import { useChartPalette } from "@/lib/theme-gradients";

export type CanvasNode = { id: string; label?: string | null; x?: number | null; y?: number | null };
export type CanvasEdge = {
  id: string;
  source: string;
  target: string;
  weight?: number;
  directed?: boolean;
};

/**
 * ノード / エッジのグラフを手描き SVG で描く(ドメイン非依存 = テンプレート還元候補)。
 * 経路図・ネットワーク図の両方に使う。本格的な図ライブラリは入れない(Phase 4 で確定)。
 *
 * - 座標(x / y)があればそのまま配置、無ければ簡易円環レイアウト
 * - highlightEdgeIds … 実線・強調色(経路 / 選んだ MST リンク)
 * - dashedEdgeIds … 破線(候補だが選ばれなかったリンク)
 * - directed なエッジには矢印
 */
export function GraphCanvas({
  nodes,
  edges,
  highlightNodeIds = [],
  highlightEdgeIds = [],
  dashedEdgeIds = [],
  width = 480,
  height = 320,
}: {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  highlightNodeIds?: string[];
  highlightEdgeIds?: string[];
  dashedEdgeIds?: string[];
  width?: number;
  height?: number;
}) {
  const mounted = useHasMounted();
  const themeSetting = useThemeSetting();
  const palette = useChartPalette(mounted ? themeSetting.resolvedTheme : undefined);

  const layout = useMemo(() => _layout(nodes, width, height), [nodes, width, height]);
  const hlNodes = new Set(highlightNodeIds);
  const hlEdges = new Set(highlightEdgeIds);
  const dashEdges = new Set(dashedEdgeIds);

  const base = palette[0] ?? "#8ab4f8";
  const accent = palette[1] ?? "#f28b82";

  return (
    <YStack borderWidth={1} borderColor="$borderColor" borderRadius="$4" padding="$2">
      <svg
        role="img"
        aria-label="graph"
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: "block", width: "100%", height: "auto" }}
      >
        <defs>
          <marker id="gc-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={accent} />
          </marker>
        </defs>

        {edges.map((e) => {
          const a = layout[e.source];
          const b = layout[e.target];
          if (!a || !b) return null;
          const highlighted = hlEdges.has(e.id);
          const dashed = dashEdges.has(e.id);
          return (
            <g key={e.id}>
              <line
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke={highlighted ? accent : base}
                strokeWidth={highlighted ? 3 : 1.5}
                strokeOpacity={dashed ? 0.35 : 0.9}
                strokeDasharray={dashed ? "4 4" : undefined}
                markerEnd={e.directed ? "url(#gc-arrow)" : undefined}
              />
              {e.weight != null ? (
                <text
                  x={(a.x + b.x) / 2}
                  y={(a.y + b.y) / 2 - 3}
                  fontSize={10}
                  fill="currentColor"
                  opacity={0.6}
                  textAnchor="middle"
                >
                  {e.weight}
                </text>
              ) : null}
            </g>
          );
        })}

        {nodes.map((n) => {
          const p = layout[n.id];
          if (!p) return null;
          const on = hlNodes.has(n.id);
          return (
            <g key={n.id}>
              <circle cx={p.x} cy={p.y} r={on ? 9 : 7} fill={on ? accent : base} stroke="currentColor" strokeWidth={0.5} />
              <text x={p.x} y={p.y - 12} fontSize={11} fill="currentColor" textAnchor="middle">
                {n.label ?? n.id}
              </text>
            </g>
          );
        })}
      </svg>
    </YStack>
  );
}

/** ノード id -> 画面座標。x/y があれば正規化して使い、無ければ円環に並べる。 */
function _layout(
  nodes: CanvasNode[],
  width: number,
  height: number,
): Record<string, { x: number; y: number }> {
  const pad = 28;
  const withCoords = nodes.filter((n) => n.x != null && n.y != null);
  if (withCoords.length === nodes.length && nodes.length > 0) {
    const xs = withCoords.map((n) => n.x as number);
    const ys = withCoords.map((n) => n.y as number);
    const [minX, maxX] = [Math.min(...xs), Math.max(...xs)];
    const [minY, maxY] = [Math.min(...ys), Math.max(...ys)];
    const spanX = maxX - minX || 1;
    const spanY = maxY - minY || 1;
    const out: Record<string, { x: number; y: number }> = {};
    for (const n of nodes) {
      out[n.id] = {
        x: pad + (((n.x as number) - minX) / spanX) * (width - 2 * pad),
        y: pad + (((n.y as number) - minY) / spanY) * (height - 2 * pad),
      };
    }
    return out;
  }
  // 円環フォールバック
  const cx = width / 2;
  const cy = height / 2;
  const r = Math.min(width, height) / 2 - pad;
  const out: Record<string, { x: number; y: number }> = {};
  nodes.forEach((n, i) => {
    const t = (i / Math.max(nodes.length, 1)) * 2 * Math.PI - Math.PI / 2;
    out[n.id] = { x: cx + r * Math.cos(t), y: cy + r * Math.sin(t) };
  });
  return out;
}
