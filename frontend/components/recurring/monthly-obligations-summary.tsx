"use client";

import { useRecurringTransactions, useLoans } from "@/lib/hooks/use-finance-data";
import { formatPaise } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { Wallet, Calendar, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RecurringTransaction } from "@/types/recurring";
import type { Loan } from "@/types/loan";

export function MonthlyObligationsSummary({ className }: { className?: string }) {
  const { recurringTransactions, loading, error, refetch } = useRecurringTransactions();
  const { loans } = useLoans();

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
        <WidgetErrorFallback title="Monthly Obligations" error={error.message} onRetry={refetch} />
      </div>
    );
  }

  const recurring = recurringTransactions || [];
  const activeRecurring = recurring.filter((r: RecurringTransaction) => r.is_active && r.type === "debit");
  
  // Calculate total monthly fixed costs
  const monthlyFixedCosts = activeRecurring.reduce((sum: number, r: RecurringTransaction) => {
    let monthly = r.amount_paise;
    if (r.frequency === "weekly") monthly = r.amount_paise * 4.33;
    if (r.frequency === "quarterly") monthly = r.amount_paise / 3;
    if (r.frequency === "annual") monthly = r.amount_paise / 12;
    return sum + monthly;
  }, 0);

  // Add loan EMIs
  const activeLoans = (loans || []).filter((l: Loan) => l.status === "active");
  const totalEMI = activeLoans.reduce((sum: number, l: Loan) => sum + (l.emi_paise || 0), 0);
  
  const totalMonthlyObligations = monthlyFixedCosts + totalEMI;

  // Count active subscriptions
  const subscriptionCount = activeRecurring.length + activeLoans.length;

  // Find upcoming dues (next 7 days)
  const today = new Date();
  const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
  
  const upcomingDues = activeRecurring.filter((r: RecurringTransaction) => {
    if (!r.next_due_date) return false;
    const dueDate = new Date(r.next_due_date);
    return dueDate >= today && dueDate <= nextWeek;
  }).length;

  return (
    <div className={cn("grid grid-cols-1 md:grid-cols-3 gap-4", className)}>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Monthly Fixed Costs</p>
              <p className="text-2xl font-bold">{formatPaise(Math.round(totalMonthlyObligations))}</p>
            </div>
            <Wallet className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active Subscriptions</p>
              <p className="text-2xl font-bold">{subscriptionCount}</p>
            </div>
            <Calendar className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Upcoming Dues (7 days)</p>
              <p className={cn("text-2xl font-bold", upcomingDues > 0 ? "text-amber-600" : "text-green-600")}>
                {upcomingDues}
              </p>
            </div>
            <AlertCircle className={cn("h-8 w-8", upcomingDues > 0 ? "text-amber-500" : "text-green-500")} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
