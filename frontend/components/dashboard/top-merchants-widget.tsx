'use client';

import { ChartContainer } from '@/components/ui/chart-container';
import { useAnalytics } from '@/lib/hooks/use-analytics';
import { Badge } from '@/components/ui/badge';

export function TopMerchantsWidget() {
  const { data, isLoading, isError, refetch } = useAnalytics();

  const merchants = data?.top_merchants || [];
  const topMerchants = merchants.slice(0, 5);

  const isEmpty = !isLoading && !isError && merchants.length === 0;

  return (
    <ChartContainer
      isLoading={isLoading}
      isError={isError}
      isEmpty={isEmpty}
      emptyMessage="No merchant data available"
      onRetry={refetch}
      title="Top Merchants"
    >
      {merchants.length > 0 && (
        <div className="space-y-1">
          {topMerchants.map((merchant, index) => (
            <div key={index} className="flex items-center justify-between text-sm py-1">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-6">
                  #{index + 1}
                </span>
                <span className="truncate">{merchant.merchant}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  {merchant.count}
                </Badge>
                <span className="font-medium text-right min-w-[60px]">
                  {merchant.amount_display}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </ChartContainer>
  );
}