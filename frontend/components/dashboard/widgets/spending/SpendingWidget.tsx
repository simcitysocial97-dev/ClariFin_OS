'use client';

import { useMemo } from 'react';
import { WidgetShell } from '@/components/dashboard/shared/widget-shell';
import { useSpending } from './hook';
import type { WidgetStatus } from '@/types/widget';

function getSpendingStatus(highestPercentage: number): WidgetStatus {
  if (highestPercentage > 50) return 'critical';
  if (highestPercentage > 30) return 'warning';
  return 'good';
}

export function SpendingWidget() {
  const { data, isLoading, error, refetch } = useSpending();

  const { categories, status, contextMessage } = useMemo(() => {
    if (!data?.summary) {
      return { categories: [], status: 'neutral' as WidgetStatus, contextMessage: '' };
    }

    const categories = data.summary.slice(0, 5);
    const highest = categories[0];
    
    let status: WidgetStatus = 'neutral';
    let contextMessage = '';

    if (highest) {
      status = getSpendingStatus(highest.percentage);
      
      // Generate conversational insight
      if (highest.percentage > 50) {
        contextMessage = `${highest.category} takes the largest share at ${highest.percentage}%`;
      } else if (highest.percentage > 30) {
        contextMessage = `${highest.category} is your top spending category`;
      } else {
        contextMessage = `Spending spread across ${categories.length} categories`;
      }
    }

    return { categories, status, contextMessage };
  }, [data]);

  const isEmpty = !isLoading && !error && categories.length === 0;

  return (
    <WidgetShell
      title="Where is my money going?"
      status={status}
      loading={isLoading}
      error={error}
      empty={isEmpty}
      onRefresh={refetch}
    >
      <div className="space-y-3">
        {contextMessage && (
          <p className="text-sm text-muted-foreground">{contextMessage}</p>
        )}
        
        {categories.map((category) => (
          <div key={category.category} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="truncate">{category.category}</span>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground text-xs">{category.count} txn</span>
                <span className="font-medium">{category.amount_display}</span>
              </div>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${Math.min(category.percentage, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </WidgetShell>
  );
}