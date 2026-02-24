'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sparkline } from '@/components/ui/sparkline';
import { CreditCard, TrendingDown, TrendingUp, Wallet, Receipt } from 'lucide-react';
import { useMemo } from 'react';
import { cn } from '@/lib/utils';

interface QuickStatsProps {
  totalSpend: string;
  thisMonth: string;
  lastMonth: string;
  monthChange: string;
  transactionCount: number;
  cardCount: number;
  monthlyChart?: Array<{ month: string; amount: number }>;
  aboveBelowAvg?: string;
  aboveAvgIsBad?: boolean;
  monthlyAverage?: string;
}

export function QuickStats({ 
  totalSpend, 
  thisMonth, 
  lastMonth, 
  monthChange,
  transactionCount,
  cardCount,
  monthlyChart,
  aboveBelowAvg,
  aboveAvgIsBad,
  monthlyAverage,
}: QuickStatsProps) {
  // Generate sparkline data from monthly chart
  const sparklineData = useMemo(() => {
    if (!monthlyChart || monthlyChart.length === 0) return [0];
    return monthlyChart.map(m => m.amount);
  }, [monthlyChart]);

  // Parse month change for trend indicator
  const changeValue = parseFloat(monthChange?.replace(/[^0-9.-]/g, '') || '0');
  const isPositiveChange = monthChange?.includes('+');
  const isNegativeChange = monthChange?.includes('-');

  // Determine subtitle color based on change direction
  const getChangeColor = () => {
    if (isNegativeChange) return 'text-green-600'; // Spending less is good
    if (isPositiveChange) return 'text-amber-600'; // Spending more is warning
    return 'text-muted-foreground';
  };

  const stats = [
    {
      title: 'Total Spend',
      value: totalSpend,
      icon: Receipt,
      description: 'All time spending',
      trend: 'neutral' as const,
      sparklineData: sparklineData,
      sparklineColor: 'hsl(var(--primary))',
    },
    {
      title: 'This Month',
      value: thisMonth,
      icon: isPositiveChange ? TrendingUp : TrendingDown,
      description: aboveBelowAvg || `vs ${lastMonth} last month`,
      descriptionColor: aboveBelowAvg 
        ? (aboveAvgIsBad ? 'text-amber-600' : 'text-green-600')
        : getChangeColor(),
      trend: isPositiveChange ? 'negative' : 'positive',
      sparklineData: sparklineData,
      sparklineColor: isPositiveChange ? 'hsl(var(--destructive))' : 'hsl(var(--primary))',
    },
    {
      title: 'Transactions',
      value: transactionCount.toString(),
      icon: Wallet,
      description: 'Total recorded',
      trend: 'neutral' as const,
      sparklineData: sparklineData,
      sparklineColor: 'hsl(var(--primary))',
    },
    {
      title: 'Cards',
      value: cardCount.toString(),
      icon: CreditCard,
      description: monthlyAverage ? `Avg: ${monthlyAverage}/mo` : 'Active statements',
      trend: 'neutral' as const,
      sparklineData: sparklineData.slice(-cardCount),
      sparklineColor: 'hsl(var(--warning))',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.title} className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
            <stat.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono tabular-nums">{stat.value}</div>
            <p className={cn("text-xs mt-1", stat.descriptionColor || 'text-muted-foreground')}>
              {stat.description}
            </p>
            {stat.sparklineData && stat.sparklineData.length > 1 && (
              <div className="mt-3">
                <Sparkline 
                  data={stat.sparklineData} 
                  color={stat.sparklineColor}
                  width={200}
                  height={30}
                />
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
