"use client";

import { useIncomeSources } from "@/lib/hooks/use-finance-data";
import { formatPaise, formatPaiseCompact } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { TrendingUp, Wallet, Award } from "lucide-react";
import { cn } from "@/lib/utils";
import type { IncomeSource } from "@/types/income";

export function IncomeSummaryCards({ className }: { className?: string }) {
  const { incomeStreams, loading, error, refetch } = useIncomeSources();

  if (loading) {
    return (
      <div className={cn("grid grid-cols-1 md:grid-cols-3 gap-4", className)}>
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4 space-y-2">
              <div className="h-3 w-32 bg-muted rounded" />
              <div className="h-8 w-28 bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <WidgetErrorFallback title="Income Summary" error={error.message} onRetry={refetch} />
      </div>
    );
  }

  const sources = incomeStreams ?? [];
  const activeSources = sources.filter((s: IncomeSource) => s.is_active);

  // Calculate total YTD income (assuming current year)
  const currentYear = new Date().getFullYear();
  const ytdIncome = activeSources.reduce((sum: number, s: IncomeSource) => {
    const startDate = s.start_date ? new Date(s.start_date) : new Date();
    if (startDate.getFullYear() === currentYear) {
      return sum + s.amount_paise;
    }
    return sum;
  }, 0);

  // Calculate average monthly income
  const monthlyIncome = activeSources.reduce((sum: number, s: IncomeSource) => {
    let monthly = s.amount_paise;
    if (s.frequency === "quarterly") monthly = s.amount_paise / 3;
    if (s.frequency === "annual") monthly = s.amount_paise / 12;
    if (s.frequency === "weekly") monthly = s.amount_paise * 4.33;
    return sum + monthly;
  }, 0);

  // Find top income source
  const topSource = activeSources.sort((a: IncomeSource, b: IncomeSource) => b.amount_paise - a.amount_paise)[0];

  return (
    <div className={cn("grid grid-cols-1 md:grid-cols-3 gap-4", className)}>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total YTD Income</p>
              <p className="text-2xl font-bold text-green-600">{formatPaise(ytdIncome)}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Avg Monthly Income</p>
              <p className="text-2xl font-bold text-blue-600">{formatPaise(Math.round(monthlyIncome))}</p>
            </div>
            <Wallet className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Top Income Source</p>
              <p className="text-lg font-bold truncate">{topSource?.name || "—"}</p>
              <p className="text-xs text-muted-foreground">
                {topSource ? formatPaiseCompact(topSource.amount_paise) : ""}
              </p>
            </div>
            <Award className="h-8 w-8 text-amber-500" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
