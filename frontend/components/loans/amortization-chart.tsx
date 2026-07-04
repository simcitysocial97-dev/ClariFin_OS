"use client";

/**
 * Amortization Chart Component
 * ============================
 *
 * Line chart showing Principal vs Interest components over loan tenure.
 * Uses Recharts for visualization.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { formatPaise } from "@/lib/format";
import type { AmortizationEntry } from "@/types/loan";

interface AmortizationChartProps {
  schedule: AmortizationEntry[];
}

interface ChartDataPoint {
  month: number;
  principal: number;
  interest: number;
  emi: number;
}

export function AmortizationChart({ schedule }: AmortizationChartProps) {
  // Transform data for the chart
  const chartData: ChartDataPoint[] = schedule.map((entry) => ({
    month: entry.period,
    principal: entry.principal_paise / 100, // Convert to rupees for cleaner axis
    interest: entry.interest_paise / 100,
    emi: entry.emi_paise / 100,
  }));

  // Custom tooltip formatter
  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean;
    payload?: Array<{ name: string; value: number; color: string }>;
    label?: number;
  }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-medium mb-2">Month {label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatPaise(entry.value * 100)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center text-muted-foreground">
        No data available for chart.
      </div>
    );
  }

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="month"
            type="number"
            tickCount={10}
            domain={[1, chartData.length]}
            label={{ value: "Month", position: "insideBottom", offset: -5 }}
          />
          <YAxis
            tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
            label={{ value: "Amount (₹)", angle: -90, position: "insideLeft" }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="principal"
            name="Principal"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="interest"
            name="Interest"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
