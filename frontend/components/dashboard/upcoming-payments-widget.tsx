"use client";

/**
 * Upcoming Payments Widget
 * ========================
 * 
 * Shows upcoming recurring transactions sorted by next due date.
 * Uses ScrollArea for internal scrolling within fixed height.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useRecurringTransactionsQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise, formatDate } from "@/lib/format";
import { ListWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { Calendar, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RecurringTransaction } from "@/types/recurring";

interface UpcomingPaymentsWidgetProps {
  mode?: "personal" | "family";
}

// Check if date is in the future
function isFutureDate(dateString: string | null): boolean {
  if (!dateString) return false;
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return date >= today;
}

// Get days until due
function getDaysUntil(dateString: string | null): number {
  if (!dateString) return 0;
  const due = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffTime = due.getTime() - today.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// Get badge variant based on urgency
function getUrgencyBadge(daysUntil: number): "default" | "secondary" | "destructive" | "outline" {
  if (daysUntil <= 3) return "destructive";
  if (daysUntil <= 7) return "secondary";
  return "outline";
}

export function UpcomingPaymentsWidget({ mode = "personal" }: UpcomingPaymentsWidgetProps) {
  const { data, loading, error, refetch } = useRecurringTransactionsQuery();

  if (loading) {
    return <ListWidgetSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Upcoming Payments"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  // Filter and sort upcoming payments
  const upcomingPayments = (data?.recurring || [])
    .filter((item: RecurringTransaction) => item.next_due_date && isFutureDate(item.next_due_date))
    .sort((a: RecurringTransaction, b: RecurringTransaction) => 
      new Date(a.next_due_date!).getTime() - new Date(b.next_due_date!).getTime()
    )
    .slice(0, 10); // Show top 10

  // Empty state
  if (upcomingPayments.length === 0) {
    return (
      <Card className="h-[320px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Upcoming Payments</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[250px] text-center px-6">
          <Calendar className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No upcoming payments found</p>
          <p className="text-muted-foreground text-xs mt-1">
            Set up recurring transactions to track upcoming bills
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Upcoming Payments
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[250px] px-6">
          <div className="space-y-3 py-2">
            {upcomingPayments.map((payment: RecurringTransaction) => {
              const daysUntil = getDaysUntil(payment.next_due_date);
              const urgencyBadge = getUrgencyBadge(daysUntil);
              
              return (
                <div
                  key={payment.id}
                  className="flex items-center justify-between py-2 border-b border-border/50 last:border-0"
                >
                  <div className="flex-1 min-w-0 mr-3">
                    <p className="text-sm font-medium truncate">
                      {payment.description}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <p className="text-xs text-muted-foreground">
                        {payment.next_due_date ? formatDate(payment.next_due_date) : 'No date'}
                      </p>
                      {daysUntil <= 7 && daysUntil >= 0 && (
                        <AlertCircle className="h-3 w-3 text-amber-500" />
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={cn(
                      "text-sm font-mono font-medium",
                      payment.type === "debit" ? "text-red-600" : "text-green-600"
                    )}>
                      {payment.type === "debit" ? "-" : "+"}
                      {formatPaise(payment.amount_paise)}
                    </span>
                    <Badge variant={urgencyBadge} className="text-[10px] px-1.5 py-0">
                      {daysUntil === 0 ? "Today" : daysUntil === 1 ? "Tomorrow" : `${daysUntil} days`}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
