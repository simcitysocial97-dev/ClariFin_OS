'use client';

import { useMemo } from 'react';
import { WidgetShell } from '@/components/dashboard/shared/widget-shell';
import { useAnalytics } from '@/lib/hooks/use-analytics';
import type { WidgetStatus } from '@/types/widget';

export function MerchantWidget() {
  const { data, isLoading, isError, refetch } = useAnalytics();

  const { merchants, status, contextMessage } = useMemo(() => {
    if (!data?.top_merchants) {
      return { merchants: [], status: 'neutral' as WidgetStatus, contextMessage: '' };
    }

    const merchants = data.top_merchants.slice(0, 5);
    
    let status: WidgetStatus = 'neutral';
    let contextMessage = '';

    if (merchants.length > 0) {
      status = 'good';
      contextMessage = `Your money goes to ${merchants.length} top merchants`;
    }

    return { merchants, status, contextMessage };
  }, [data]);

  const isEmpty = !isLoading && !isError && merchants.length === 0;

  return (
    <WidgetShell
      title="Who receives my money?"
      status={status}
      loading={isLoading}
      error={isError ? new Error('Failed to load merchant data') : null}
      empty={isEmpty}
      onRefresh={refetch}
    >
      <div className="space-y-3">
        {contextMessage && (
          <p className="text-sm text-muted-foreground">{contextMessage}</p>
        )}
        
        {merchants.map((merchant, index) => (
          <div key={merchant.merchant} className="flex items-center justify-between text-sm py-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground w-6">
                #{index + 1}
              </span>
              <span className="truncate">{merchant.merchant}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-xs">{merchant.count} txn</span>
              <span className="font-medium text-right min-w-[60px]">
                {merchant.amount_display}
              </span>
            </div>
          </div>
        ))}
      </div>
    </WidgetShell>
  );
}