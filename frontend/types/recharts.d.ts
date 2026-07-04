import "recharts";
import { CSSProperties } from "react";

declare module "recharts" {
  interface CategoricalChartProps {
    className?: string;
    style?: CSSProperties;
  }
}

// Type helper for dynamic imports with Next.js
declare module "recharts" {
  // Export component types for use in dynamic imports
  export type BarComponent = typeof import("recharts").Bar;
  export type PieComponent = typeof import("recharts").Pie;
  export type XAxisComponent = typeof import("recharts").XAxis;
  export type YAxisComponent = typeof import("recharts").YAxis;
  export type TooltipComponent = typeof import("recharts").Tooltip;
  export type LegendComponent = typeof import("recharts").Legend;
  export type AreaComponent = typeof import("recharts").Area;
  export type LineComponent = typeof import("recharts").Line;
  export type CellComponent = typeof import("recharts").Cell;
  export type CartesianGridComponent = typeof import("recharts").CartesianGrid;
  export type ResponsiveContainerComponent = typeof import("recharts").ResponsiveContainer;
  export type PieChartComponent = typeof import("recharts").PieChart;
  export type BarChartComponent = typeof import("recharts").BarChart;
  export type LineChartComponent = typeof import("recharts").LineChart;
  export type AreaChartComponent = typeof import("recharts").AreaChart;
  export type ComposedChartComponent = typeof import("recharts").ComposedChart;
}
