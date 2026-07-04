'use client';

import { useEffect, useState } from 'react';

// Dynamically import recharts to avoid SSR issues
import dynamic from 'next/dynamic';

const BarChart = dynamic(() => import('recharts').then((mod) => mod.BarChart), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const Bar = dynamic(() => import('recharts').then((mod) => mod.Bar), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), { ssr: false });

interface BankChartItem {
  bank: string;
  amount: number;
}

interface BankWiseChartProps {
  bankChart: BankChartItem[];
}

export function BankWiseChart({ bankChart }: BankWiseChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Sort and limit to top 6 banks
  const data = bankChart
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 6);

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        No bank data available.
      </div>
    );
  }

  if (!mounted) {
    return <div className="h-[200px] flex items-center justify-center text-sm text-muted-foreground">Loading chart...</div>;
  }

  return (
    <div className="h-[200px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 80, right: 20, top: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground) / 0.2)" horizontal={true} vertical={false} />
          <XAxis 
            type="number" 
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} 
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
          />
          <YAxis 
            type="category" 
            dataKey="bank" 
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} 
            width={70}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--popover))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
              color: 'hsl(var(--popover-foreground))',
              fontSize: '12px',
            }}
            formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Amount']}
          />
          <Bar 
            dataKey="amount" 
            fill="hsl(var(--primary))" 
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
