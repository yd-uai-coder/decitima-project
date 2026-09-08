// DeciTima samples │ Phase 3
"use client";

import { Text, XStack, YStack } from "tamagui";
import { useThemeSetting } from "@tamagui/next-theme";
import { useChartPalette } from "@/lib/theme-gradients";
import { useHasMounted } from "@/hooks/useHasMounted";

export type LineSeries = { label: string; points: number[] };

/**
 * 軸・凡例つき多系列ラインチャート(ドメイン非依存)。対数 y 軸オプションつき ──
 * 入力サイズ別カーブ(全探索が指数的に伸びる)を見るのに対数軸が要る。テンプレート還元候補。
 *
 * xLabels: x 軸の目盛りラベル(= points のインデックスに対応)。
 */
export function MultiLineChart({
  xLabels,
  series,
  width = 420,
  height = 200,
  logScale = false,
  yTicks = 4,
  valueFormat = (v: number) => v.toPrecision(3),
}: {
  xLabels: (string | number)[];
  series: LineSeries[];
  width?: number;
  height?: number;
  logScale?: boolean;
  yTicks?: number;
  valueFormat?: (v: number) => string;
}) {
  const themeSetting = useThemeSetting();
  const mounted = useHasMounted();
  const palette = useChartPalette(mounted ? themeSetting.resolvedTheme : undefined);

  const padLeft = 48;
  const padBottom = 22;
  const plotW = width - padLeft;
  const plotH = height - padBottom;

  const all = series.flatMap((s) => s.points).filter((v) => v > 0 || !logScale);
  const rawMax = Math.max(...series.flatMap((s) => s.points), 1);
  const rawMin = logScale ? Math.max(Math.min(...all, rawMax), 1) : 0;

  const scaleY = (v: number) => {
    if (logScale) {
      const lo = Math.log10(rawMin);
      const hi = Math.log10(rawMax);
      const t = hi === lo ? 1 : (Math.log10(Math.max(v, 1)) - lo) / (hi - lo);
      return plotH - t * plotH;
    }
    return plotH - (v / rawMax) * plotH;
  };
  const scaleX = (i: number) => padLeft + (i / Math.max(xLabels.length - 1, 1)) * plotW;

  const ticks = Array.from({ length: yTicks + 1 }, (_, i) => {
    if (logScale) {
      const lo = Math.log10(rawMin);
      const hi = Math.log10(rawMax);
      return 10 ** (lo + ((hi - lo) / yTicks) * i);
    }
    return (rawMax / yTicks) * i;
  });

  return (
    <YStack gap="$2">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: "block", maxWidth: "100%" }}
        role="img"
      >
        {ticks.map((t, i) => {
          const y = scaleY(t);
          return (
            <g key={i}>
              <line x1={padLeft} y1={y} x2={width} y2={y} stroke="currentColor" opacity={0.12} />
              <text x={padLeft - 6} y={y + 3} fontSize={9} textAnchor="end" fill="currentColor">
                {valueFormat(t)}
              </text>
            </g>
          );
        })}
        {series.map((s, si) => (
          <polyline
            key={s.label}
            fill="none"
            stroke={palette[si % palette.length]}
            strokeWidth={2}
            points={s.points.map((v, i) => `${scaleX(i)},${scaleY(v)}`).join(" ")}
          />
        ))}
        {xLabels.map((label, i) => (
          <text
            key={i}
            x={scaleX(i)}
            y={height - 6}
            fontSize={9}
            textAnchor="middle"
            fill="currentColor"
          >
            {label}
          </text>
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
