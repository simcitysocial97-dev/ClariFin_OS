'use client';

import { useEffect, useState } from 'react';
import { formatINR } from '@/lib/utils/format';

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

// Value is in paise (canonical)
interface CategoryChartItem {
  name: string;
  amount_paise: number;  // paise
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
    .map(item => ({ name: item.name, value: item.amount_paise }))
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

  // Format paise value for chart display (convert to rupees for K/L formatting)
  const formatPaiseForChart = (paise: number) => {
    const rupees = paise / 100;
    if (rupees >= 100000) {
      return `₹${(rupees / 100000).toFixed(0)}L`;
    }
    if (rupees >= 1000) {
      return `₹${(rupees / 1000).toFixed(0)}K`;
    }
    return `₹${rupees}`;
  };

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
            tickFormatter={formatPaiseForChart}
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
            formatter={(value) => [formatINR(value as number), 'Amount']}
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
