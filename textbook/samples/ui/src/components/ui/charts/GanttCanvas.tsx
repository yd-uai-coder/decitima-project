// DeciTima samples │ Phase 8
"use client";

import { useThemeSetting } from "@tamagui/next-theme";
import { YStack } from "tamagui";
import { useHasMounted } from "@/hooks/useHasMounted";
import { useChartPalette } from "@/lib/theme-gradients";

export type GanttBar = {
  id: string;
  label?: string | null;
  start: number;
  end: number;
  /** end からさらに右へ伸ばす「余裕」(slack)。0 なら描かない */
  slack?: number;
  /** 強調(クリティカルパス上のタスクなど) */
  highlight?: boolean;
};

/**
 * 時間軸に沿った横バーのタイムライン(ドメイン非依存 = テンプレート還元候補)。
 * ガントチャート / スケジュール可視化に使う。図ライブラリは入れない(GraphCanvas と同じ方針)。
 *
 * - bars … 1 本 = 1 行。start/end で位置と長さを決める(整数時間単位を想定)
 * - highlight … 強調色(クリティカルパス)
 * - slack … バーの右に薄い延長を描く(このタスクを何単位まで遅らせられるか)
 */
export function GanttCanvas({
  bars,
  horizon,
  rowHeight = 26,
  width = 520,
}: {
  bars: GanttBar[];
  horizon?: number;
  rowHeight?: number;
  width?: number;
}) {
  const mounted = useHasMounted();
  const themeSetting = useThemeSetting();
  const palette = useChartPalette(mounted ? themeSetting.resolvedTheme : undefined);
  const base = palette[0] ?? "#8ab4f8";
  const accent = palette[1] ?? "#f28b82";

  const span = Math.max(horizon ?? Math.max(1, ...bars.map((b) => b.end + (b.slack ?? 0))), 1);
  const labelW = 90;
  const padX = 8;
  const chartW = width - labelW - padX * 2;
  const height = bars.length * rowHeight + 24;
  const x = (t: number) => labelW + padX + (t / span) * chartW;

  const ticks = Array.from({ length: span + 1 }, (_, i) => i).filter(
    (i) => span <= 12 || i % Math.ceil(span / 12) === 0,
  );

  return (
    <YStack borderWidth={1} borderColor="$borderColor" borderRadius="$4" padding="$2">
      <svg
        role="img"
        aria-label="gantt chart"
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: "block", width: "100%", height: "auto" }}
      >
        {ticks.map((t) => (
          <g key={`tick-${t}`}>
            <line
              x1={x(t)}
              y1={16}
              x2={x(t)}
              y2={height - 4}
              stroke="currentColor"
              strokeOpacity={0.12}
            />
            <text x={x(t)} y={10} fontSize={9} fill="currentColor" opacity={0.5} textAnchor="middle">
              {t}
            </text>
          </g>
        ))}

        {bars.map((b, i) => {
          const y = 20 + i * rowHeight;
          const barX = x(b.start);
          const barW = Math.max(x(b.end) - barX, 2);
          return (
            <g key={b.id}>
              <text x={4} y={y + rowHeight * 0.55} fontSize={11} fill="currentColor">
                {b.label ?? b.id}
              </text>
              {b.slack && b.slack > 0 ? (
                <rect
                  x={x(b.end)}
                  y={y + 4}
                  width={Math.max(x(b.end + b.slack) - x(b.end), 1)}
                  height={rowHeight - 12}
                  fill={base}
                  opacity={0.18}
                  rx={2}
                />
              ) : null}
              <rect
                x={barX}
                y={y + 3}
                width={barW}
                height={rowHeight - 10}
                fill={b.highlight ? accent : base}
                opacity={b.highlight ? 0.95 : 0.75}
                rx={3}
              />
              <text
                x={barX + 4}
                y={y + rowHeight * 0.55}
                fontSize={9}
                fill="currentColor"
                opacity={0.7}
              >
                {b.start}–{b.end}
              </text>
            </g>
          );
        })}
      </svg>
    </YStack>
  );
}
