"use client";

/**
 * Asset Allocation Widget
 * =======================
 * 
 * Donut chart showing portfolio breakdown by category.
 * Uses Recharts PieChart for the visualization.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAssetAllocationQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise } from "@/lib/format";
import { DonutChartSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer,
  Tooltip
} from "recharts";
import { PieChart as PieChartIcon } from "lucide-react";

interface AssetAllocationWidgetProps {
  mode?: "personal" | "family";
}

interface AllocationItem {
  category: string;
  value_paise: number;
  percentage: number;
}

// Color palette for chart segments
const COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
  "hsl(var(--primary))",
  "hsl(var(--secondary))",
  "hsl(var(--accent))",
];

// Custom tooltip
function CustomTooltip({ active, payload }: { 
  active?: boolean; 
  payload?: Array<{ name: string; value: number; payload: AllocationItem }>;
}) {
  if (active && payload && payload.length) {
    const data = payload[0]?.payload;
    if (!data) return null;
    return (
      <div className="bg-popover border rounded-lg p-3 shadow-lg">
        <p className="font-medium text-sm">{data.category}</p>
        <p className="text-sm text-muted-foreground">
          {formatPaise(data.value_paise)} ({data.percentage.toFixed(1)}%)
        </p>
      </div>
    );
  }
  return null;
}

export function AssetAllocationWidget({ mode = "personal" }: AssetAllocationWidgetProps) {
  const { data, loading, error, refetch } = useAssetAllocationQuery();

  if (loading) {
    return <DonutChartSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Asset Allocation"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  const allocation: AllocationItem[] = data?.allocation || [];

  // Empty state
  if (allocation.length === 0) {
    return (
      <Card className="h-[320px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Asset Allocation</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[250px] text-center">
          <PieChartIcon className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No allocation data available</p>
          <p className="text-muted-foreground text-xs mt-1">
            Add investments to see your portfolio breakdown
          </p>
        </CardContent>
      </Card>
    );
  }

  // Transform data for Recharts
  const chartData = allocation.map((item) => ({
    name: item.category,
    value: item.value_paise,
    ...item,
  }));

  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Asset Allocation
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <div className="h-[140px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={65}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((_entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={COLORS[index % COLORS.length]} 
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        {/* Custom Legend */}
        <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 w-full px-2">
          {allocation.slice(0, 6).map((item, index) => (
            <div key={item.category} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <div className="min-w-0 flex-1">
                <p className="text-xs truncate">{item.category}</p>
                <p className="text-[10px] text-muted-foreground">
                  {item.percentage.toFixed(0)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
