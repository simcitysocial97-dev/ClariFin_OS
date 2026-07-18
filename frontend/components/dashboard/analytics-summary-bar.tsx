'use client';

import { useOverview } from '@/lib/hooks/use-overview';
import { useAnalytics } from '@/lib/hooks/use-analytics';
import { Separator } from '@/components/ui/separator';
import { DataStateWrapper } from '@/components/ui/data-state-wrapper';

export function AnalyticsSummaryBar() {
  const { data: overviewData, isLoading: overviewLoading, isError: overviewError, refetch: refetchOverview } = useOverview();
  const { data: analyticsData, isLoading: analyticsLoading, isError: analyticsError, refetch: refetchAnalytics } = useAnalytics();

  const isLoading = overviewLoading || analyticsLoading;
  const isError = overviewError || analyticsError;
  const isEmpty = !overviewData && !analyticsData;

  return (
    <DataStateWrapper
      isLoading={isLoading}
      isError={isError}
      isEmpty={isEmpty}
      onRetry={() => {
        refetchOverview();
        refetchAnalytics();
      }}
    >
      <div className="flex items-center justify-between px-4 py-2 bg-muted/30 rounded-lg">
        <div className="flex-1 text-center">
          <p className="text-xs text-muted-foreground">Transactions</p>
          <p className="text-sm font-semibold">{overviewData?.transaction_count ?? 0}</p>
        </div>
        
        <Separator orientation="vertical" className="h-8" />
        
        <div className="flex-1 text-center">
          <p className="text-xs text-muted-foreground">Merchants</p>
          <p className="text-sm font-semibold">{analyticsData?.unique_merchants ?? 0}</p>
        </div>
        
        <Separator orientation="vertical" className="h-8" />
        
        <div className="flex-1 text-center">
          <p className="text-xs text-muted-foreground">Months</p>
          <p className="text-sm font-semibold">{overviewData?.months_of_data ?? 0}</p>
        </div>
        
        <Separator orientation="vertical" className="h-8" />
        
        <div className="flex-1 text-center">
          <p className="text-xs text-muted-foreground">Peak Month</p>
          <p className="text-sm font-semibold">{analyticsData?.highest_month ?? '—'}</p>
        </div>
      </div>
    </DataStateWrapper>
  );
}