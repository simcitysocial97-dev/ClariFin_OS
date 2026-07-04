'use client';

import { useEffect, useState } from 'react';

// Dynamically import recharts to avoid SSR issues
import dynamic from 'next/dynamic';

// @ts-ignore - recharts types are incompatible with next/dynamic
const BarChart = dynamic(() => import('recharts').then((mod) => mod.BarChart), { ssr: false, loading: () => null });
// @ts-ignore - recharts types are incompatible with next/dynamic
const Bar = dynamic(() => import('recharts').then((mod) => mod.Bar), { ssr: false, loading: () => null });
// @ts-ignore - recharts types are incompatible with next/dynamic
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false, loading: () => null });
// @ts-ignore - recharts types are incompatible with next/dynamic
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false, loading: () => null });
// @ts-ignore - recharts types are incompatible with next/dynamic
const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), { ssr: false, loading: () => null });
// @ts-ignore - recharts types are incompatible with next/dynamic
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false, loading: () => null });
// @ts-ignore - recharts types are incompatible with next/dynamic
const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), { ssr: false, loading: () => null });

interface CategoryChartItem {
  name: string;
  value: number;
}

interface SpendingOverviewProps {
  categoryChart: CategoryChartItem[];
}

export function SpendingOverview({ categoryChart }: SpendingOverviewProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Sort and limit to top 8 categories
  const data = categoryChart
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        No spending data available.
      </div>
    );
  }

  if (!mounted) {
    return <div className="h-[300px] flex items-center justify-center text-sm text-muted-foreground">Loading chart...</div>;
  }

  return (
    <div className="h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart 
          data={data} 
          layout="vertical" 
          margin={{ left: 100, right: 20, top: 10, bottom: 10 }}
        >
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="hsl(var(--muted-foreground) / 0.2)" 
            horizontal={true} 
            vertical={false} 
          />
          <XAxis 
            type="number" 
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} 
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
          />
          <YAxis 
            type="category" 
            dataKey="name" 
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} 
            width={90}
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
            dataKey="value" 
            fill="hsl(var(--primary))" 
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
