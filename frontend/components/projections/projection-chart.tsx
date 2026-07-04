"use client";

/**
 * Projection Chart Component
 * ==========================
 * Reusable area/line chart for projections with multiple data series
 */

import dynamic from "next/dynamic";
import { formatPaise } from "@/lib/format";

// Dynamically import Recharts to avoid SSR issues
const ResponsiveContainer = dynamic(
  () => import("recharts").then((mod) => mod.ResponsiveContainer),
  { ssr: false }
);
const AreaChart = dynamic(
  () => import("recharts").then((mod) => mod.AreaChart),
  { ssr: false }
);
// @ts-expect-error - Recharts dynamic import type mismatch
const Area = dynamic(() => import("recharts").then((mod) => mod.Area), {
  ssr: false,
});
// @ts-expect-error - Recharts dynamic import type mismatch
const Line = dynamic(() => import("recharts").then((mod) => mod.Line), {
  ssr: false,
});
// @ts-expect-error - Recharts dynamic import type mismatch
const XAxis = dynamic(() => import("recharts").then((mod) => mod.XAxis), {
  ssr: false,
});
// @ts-expect-error - Recharts dynamic import type mismatch
const YAxis = dynamic(() => import("recharts").then((mod) => mod.YAxis), {
  ssr: false,
});
const CartesianGrid = dynamic(
  () => import("recharts").then((mod) => mod.CartesianGrid),
  { ssr: false }
);
// @ts-expect-error - Recharts dynamic import type mismatch
const Tooltip = dynamic(() => import("recharts").then((mod) => mod.Tooltip), {
  ssr: false,
});
// @ts-expect-error - Recharts dynamic import type mismatch
const Legend = dynamic(() => import("recharts").then((mod) => mod.Legend), {
  ssr: false,
});

interface DataPoint {
  month: string;
  [key: string]: string | number;
}

interface LineConfig {
  key: string;
  name: string;
  color: string;
  type?: "line" | "area";
  strokeWidth?: number;
}

interface ProjectionChartProps {
  data: DataPoint[];
  lines: LineConfig[];
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  yAxisFormatter?: (value: number) => string;
}

export function ProjectionChart({
  data,
  lines,
  height = 400,
  showGrid = true,
  showLegend = true,
  yAxisFormatter = (value) => formatPaise(value),
}: ProjectionChartProps) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => {
              const date = new Date(value);
              return `${date.toLocaleString("default", { month: "short" })} '${date.getFullYear().toString().slice(-2)}`;
            }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={yAxisFormatter}
            width={80}
          />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any, name: any) => [
              formatPaise(Number(value)),
              String(name),
            ]}
            labelFormatter={(label) => {
              const date = new Date(label);
              return date.toLocaleDateString("en-IN", {
                month: "long",
                year: "numeric",
              });
            }}
          />
          {showLegend && <Legend />}
          {lines.map((line) =>
            line.type === "area" ? (
              <Area
                key={line.key}
                type="monotone"
                dataKey={line.key}
                name={line.name}
                stroke={line.color}
                fill={line.color}
                fillOpacity={0.1}
                strokeWidth={line.strokeWidth || 2}
              />
            ) : (
              <Line
                key={line.key}
                type="monotone"
                dataKey={line.key}
                name={line.name}
                stroke={line.color}
                strokeWidth={line.strokeWidth || 2}
                dot={false}
              />
            )
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
