"use client";

/**
 * Assets & Liabilities Columns
 * ============================
 *
 * Two-column layout showing Asset accounts (left) and Liability accounts (right).
 * Uses shadcn Card and ScrollArea for a polished look.
 */

import { useNetWorth } from "@/lib/hooks/use-finance-data";
import { formatPaise } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { Wallet, CreditCard, Landmark, PiggyBank, TrendingDown, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface AssetsLiabilitiesColumnsProps {
  className?: string;
}

// Icon mapping for different account types
const assetIcons: Record<string, React.ReactNode> = {
  bank: <Wallet className="h-4 w-4" />,
  savings: <Wallet className="h-4 w-4" />,
  investment: <TrendingDown className="h-4 w-4" />,
  fd: <PiggyBank className="h-4 w-4" />,
  fixed_deposit: <PiggyBank className="h-4 w-4" />,
  default: <Landmark className="h-4 w-4" />,
};

const liabilityIcons: Record<string, React.ReactNode> = {
  credit_card: <CreditCard className="h-4 w-4" />,
  loan: <TrendingDown className="h-4 w-4" />,
  credit: <CreditCard className="h-4 w-4" />,
  default: <ArrowDownRight className="h-4 w-4" />,
};

interface BreakdownItem {
  paise: number;
  percentage: number;
}

interface BreakdownData {
  [key: string]: BreakdownItem;
}

function AssetsColumn({ data }: { data: BreakdownData }) {
  const entries = Object.entries(data);
  const totalPaise = entries.reduce((sum, [, value]) => sum + (value.paise || 0), 0);

  return (
    <Card className="h-full border-green-200/50 dark:border-green-900/30">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <ArrowUpRight className="h-4 w-4 text-green-600" />
          Assets
          <span className="ml-auto text-green-600">{formatPaise(totalPaise)}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[280px]">
          <div className="space-y-3 pr-4">
            {entries.length === 0 ? (
              <p className="text-muted-foreground text-sm text-center py-8">
                No asset data available
              </p>
            ) : (
              entries.map(([key, value]) => {
                const icon = assetIcons[key.toLowerCase()] || assetIcons.default;
                return (
                  <div
                    key={key}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-md bg-green-100/50 dark:bg-green-900/20 text-green-600">
                        {icon}
                      </div>
                      <span className="capitalize font-medium">
                        {key.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="font-semibold block">
                        {formatPaise(value.paise)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {value.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function LiabilitiesColumn({ data }: { data: BreakdownData }) {
  const entries = Object.entries(data);
  const totalPaise = entries.reduce((sum, [, value]) => sum + (value.paise || 0), 0);

  return (
    <Card className="h-full border-red-200/50 dark:border-red-900/30">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <ArrowDownRight className="h-4 w-4 text-red-600" />
          Liabilities
          <span className="ml-auto text-red-600">{formatPaise(totalPaise)}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[280px]">
          <div className="space-y-3 pr-4">
            {entries.length === 0 ? (
              <p className="text-muted-foreground text-sm text-center py-8">
                No liability data available
              </p>
            ) : (
              entries.map(([key, value]) => {
                const icon = liabilityIcons[key.toLowerCase()] || liabilityIcons.default;
                return (
                  <div
                    key={key}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-md bg-red-100/50 dark:bg-red-900/20 text-red-600">
                        {icon}
                      </div>
                      <span className="capitalize font-medium">
                        {key.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="font-semibold block">
                        {formatPaise(value.paise)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {value.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

export function AssetsLiabilitiesColumns({ className }: AssetsLiabilitiesColumnsProps) {
  const { data, loading, error, refetch } = useNetWorth();

  if (loading) {
    return (
      <div className={cn("grid grid-cols-1 md:grid-cols-2 gap-6", className)}>
        <Card className="h-[400px]">
          <CardHeader className="pb-3">
            <div className="h-5 w-20 bg-muted rounded animate-pulse" />
          </CardHeader>
          <CardContent className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center justify-between p-2">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 bg-muted rounded animate-pulse" />
                  <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                </div>
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
              </div>
            ))}
          </CardContent>
        </Card>
        <Card className="h-[400px]">
          <CardHeader className="pb-3">
            <div className="h-5 w-24 bg-muted rounded animate-pulse" />
          </CardHeader>
          <CardContent className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center justify-between p-2">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 bg-muted rounded animate-pulse" />
                  <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                </div>
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <WidgetErrorFallback
          title="Assets & Liabilities"
          error={error.message}
          onRetry={refetch}
        />
      </div>
    );
  }

  const assetBreakdown = (data?.asset_breakdown || {}) as BreakdownData;
  const liabilityBreakdown = (data?.liability_breakdown || {}) as BreakdownData;

  return (
    <div className={cn("grid grid-cols-1 md:grid-cols-2 gap-6", className)}>
      <AssetsColumn data={assetBreakdown} />
      <LiabilitiesColumn data={liabilityBreakdown} />
    </div>
  );
}
