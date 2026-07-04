"use client";

/**
 * Asset Allocation Chart Component
 * ================================
 *
 * Donut chart showing investment allocation by type
 * with legend table below
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPaise } from "@/lib/format";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import dynamic from "next/dynamic";

const PieChart = dynamic(() => import("recharts").then((mod) => mod.PieChart), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const Pie = dynamic(() => import("recharts").then((mod) => mod.Pie), { ssr: false });
const Cell = dynamic(() => import("recharts").then((mod) => mod.Cell), { ssr: false });
const ResponsiveContainer = dynamic(() => import("recharts").then((mod) => mod.ResponsiveContainer), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const Tooltip = dynamic(() => import("recharts").then((mod) => mod.Tooltip), { ssr: false });

interface AllocationItem {
  category: string;
  value_paise: number;
  percentage: number;
}

interface AllocationChartProps {
  allocation: AllocationItem[] | null;
}

const COLORS = [
  "#3B82F6", // Blue
  "#10B981", // Green
  "#F59E0B", // Amber
  "#EF4444", // Red
  "#8B5CF6", // Violet
  "#EC4899", // Pink
  "#06B6D4", // Cyan
  "#84CC16", // Lime
  "#F97316", // Orange
  "#6366F1", // Indigo
];

export function AllocationChart({ allocation }: AllocationChartProps) {
  if (!allocation || allocation.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-lg">Asset Allocation</CardTitle>
        </CardHeader>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">No allocation data available</p>
        </CardContent>
      </Card>
    );
  }

  const chartData = allocation.map((item) => ({
    name: item.category,
    value: item.value_paise / 100,
    percentage: item.percentage,
  }));

  const totalValue = allocation.reduce((sum, item) => sum + item.value_paise, 0);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">Asset Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Chart */}
        <div className="h-64 mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {chartData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => [
                  new Intl.NumberFormat("en-IN", {
                    style: "currency",
                    currency: "INR",
                    minimumFractionDigits: 2,
                  }).format(Number(value)),
                  "",
                ]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend Table */}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Category</TableHead>
              <TableHead className="text-right">Value</TableHead>
              <TableHead className="text-right">%</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {allocation.map((item, index) => (
              <TableRow key={item.category}>
                <TableCell className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="capitalize">{item.category.replace(/_/g, " ")}</span>
                </TableCell>
                <TableCell className="text-right">{formatPaise(item.value_paise)}</TableCell>
                <TableCell className="text-right">{item.percentage.toFixed(1)}%</TableCell>
              </TableRow>
            ))}
            <TableRow className="font-semibold">
              <TableCell>Total</TableCell>
              <TableCell className="text-right">{formatPaise(totalValue)}</TableCell>
              <TableCell className="text-right">100%</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
