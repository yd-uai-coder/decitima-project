// DeciTima samples │ Phase 3
"use client";

import { Text, XStack, YStack } from "tamagui";
import { useThemeSetting } from "@tamagui/next-theme";
import { useChartPalette } from "@/lib/theme-gradients";
import { useHasMounted } from "@/hooks/useHasMounted";

export type BarSeries = { label: string; values: number[] };

/**
 * 軸・凡例つきのグループ棒グラフ(ドメイン非依存)。既存の手描き SVG(BarChart)を
 * y 軸目盛り + 凡例 + 系列(グループ内の複数棒)に拡張したもの。テンプレート還元候補。
 *
 * groups: グループ名(x 軸ラベル)。series: 系列。series[i].values[j] が
 * group j における系列 i の値。
 */
export function GroupedBarChart({
  groups,
  series,
  width = 420,
  height = 200,
  yTicks = 4,
  valueFormat = (v: number) => v.toPrecision(3),
}: {
  groups: string[];
  series: BarSeries[];
  width?: number;
  height?: number;
  yTicks?: number;
  valueFormat?: (v: number) => string;
}) {
  const themeSetting = useThemeSetting();
  const mounted = useHasMounted();
  const palette = useChartPalette(mounted ? themeSetting.resolvedTheme : undefined);

  const padLeft = 44;
  const padBottom = 22;
  const plotW = width - padLeft;
  const plotH = height - padBottom;
  const allValues = series.flatMap((s) => s.values);
  const max = Math.max(...allValues, 1);
  const groupW = plotW / groups.length;
  const barW = (groupW * 0.7) / Math.max(series.length, 1);

  const ticks = Array.from({ length: yTicks + 1 }, (_, i) => (max / yTicks) * i);

  return (
    <YStack gap="$2">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: "block", maxWidth: "100%" }}
        role="img"
      >
        {ticks.map((t) => {
          const y = plotH - (t / max) * plotH;
          return (
            <g key={t}>
              <line x1={padLeft} y1={y} x2={width} y2={y} stroke="currentColor" opacity={0.12} />
              <text x={padLeft - 6} y={y + 3} fontSize={9} textAnchor="end" fill="currentColor">
                {valueFormat(t)}
              </text>
            </g>
          );
        })}
        {groups.map((g, gi) => (
          <g key={g}>
            {series.map((s, si) => {
              const v = s.values[gi] ?? 0;
              const barH = (v / max) * plotH;
              const x = padLeft + gi * groupW + groupW * 0.15 + si * barW;
              return (
                <rect
                  key={s.label}
                  x={x}
                  y={plotH - barH}
                  width={Math.max(barW - 2, 1)}
                  height={Math.max(barH, 1)}
                  fill={palette[si % palette.length]}
                  rx={2}
                />
              );
            })}
            <text
              x={padLeft + gi * groupW + groupW / 2}
              y={height - 6}
              fontSize={9}
              textAnchor="middle"
              fill="currentColor"
            >
              {g}
            </text>
          </g>
        ))}
      </svg>
      <XStack gap="$3" flexWrap="wrap">
        {series.map((s, si) => (
          <XStack key={s.label} alignItems="center" gap="$1.5">
            <YStack width={10} height={10} borderRadius={3} backgroundColor={palette[si % palette.length]} />
            <Text fontSize="$1" color="$color11">
              {s.label}
            </Text>
          </XStack>
        ))}
      </XStack>
    </YStack>
  );
}
