'use client';

import { ChartContainer } from '@/components/ui/chart-container';
import { useAnalytics } from '@/lib/hooks/use-analytics';
import { truncateText } from '@/lib/utils/format';

interface RecurringCharge {
  description: string;
  frequency: number;
  avg_display: string;
  annual_display: string;
}

export function RecurringChargesWidget() {
  const { data, isLoading, isError, refetch } = useAnalytics();

  const charges = data?.recurring_charges || [];
  const topCharges = charges.slice(0, 5);
  
  // Calculate total annual cost
  const totalAnnual = charges.reduce((sum, charge) => {
    const amount = parseFloat(charge.annual_display.replace(/[₹,]/g, '')) || 0;
    return sum + amount;
  }, 0);

  const isEmpty = !isLoading && !isError && charges.length === 0;

  return (
    <ChartContainer
      isLoading={isLoading}
      isError={isError}
      isEmpty={isEmpty}
      emptyMessage="No recurring charges detected"
      onRetry={refetch}
      title="Recurring Charges"
    >
      {charges.length > 0 && (
        <div className="space-y-1">
          {topCharges.map((charge, index) => (
            <div key={index} className="flex items-center justify-between text-sm py-1">
              <div className="flex-1 min-w-0">
                <p className="truncate" title={charge.description}>
                  {truncateText(charge.description, 30)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {charge.frequency}×/month
                </p>
              </div>
              <div className="text-right">
                <p className="font-medium">{charge.avg_display}</p>
                <p className="text-xs text-muted-foreground">{charge.annual_display}</p>
              </div>
            </div>
          ))}
          
          {/* Total annual footer */}
          <div className="pt-2 mt-2 border-t">
            <div className="flex justify-between items-center">
              <span className="text-xs text-muted-foreground">Total Annual</span>
              <span className="text-sm font-semibold">
                ₹{totalAnnual.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </span>
            </div>
          </div>
        </div>
      )}
    </ChartContainer>
  );
}