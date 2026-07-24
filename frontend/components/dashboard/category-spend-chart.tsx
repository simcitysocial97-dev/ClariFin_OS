'use client';

import { useEffect, useState } from 'react';
import { ChartContainer } from '@/components/ui/chart-container';
import { ExplainButton } from '@/components/ui/explain-button';
import { useOverview } from '@/lib/hooks/use-overview';
import { formatINRCompact } from '@/lib/utils/format';

// Dynamically import recharts to avoid SSR issues
import dynamic from 'next/dynamic';

const BarChart = dynamic(() => import('recharts').then((mod) => mod.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then((mod) => mod.Bar), { ssr: false });
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), { ssr: false });

export function CategorySpendChart() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { data, isLoading, isError, refetch } = useOverview();

  const categories = data?.category_chart || [];
  // Sort descending by value and limit to 8
  const sortedCategories = [...categories]
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  const isEmpty = !data || sortedCategories.length === 0;

  if (!mounted) {
    return (
      <ChartContainer isLoading={true} isError={false} isEmpty={false} children={null} />
    );
  }

  return (
    <div className="w-full">
      <div className="mb-3 flex items-center justify-end">
        <ExplainButton
          title="Category Spend"
          explanation="Breakdown of your spending by category. Helps identify where your money goes and spot opportunities to optimize your budget."
        />
      </div>
      <ChartContainer
        isLoading={isLoading}
        isError={isError}
        isEmpty={isEmpty}
        onRetry={refetch}
        title="Category Spend"
      >
        {sortedCategories.length > 0 && (
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={sortedCategories}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 80, bottom: 10 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="hsl(var(--muted-foreground) / 0.2)"
                  horizontal={false}
                />
                <XAxis
                  type="number"
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(value) => formatINRCompact(Number(value))}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={75}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--popover-foreground))',
                    fontSize: '12px',
                  }}
                  formatter={(value) => [formatINRCompact(Number(value)), 'Amount']}
                />
                <Bar
                  dataKey="value"
                  name="Spending"
                  fill="hsl(var(--primary))"
                  radius={[0, 4, 4, 0]}
                  barSize={20}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </ChartContainer>
    </div>
  );
}