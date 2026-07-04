"use client";

import { useRecurringTransactions, useLoans } from "@/lib/hooks/use-finance-data";
import { formatPaise } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { CreditCard, Home, Bell } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RecurringTransaction } from "@/types/recurring";
import type { Loan } from "@/types/loan";

export function UpcomingBillsTimeline({ className }: { className?: string }) {
  const { recurringTransactions, loading, error, refetch } = useRecurringTransactions();
  const { loans } = useLoans();

  if (loading) {
    return (
      <Card className={cn("h-[400px]", className)}>
        <CardHeader className="pb-2">
          <div className="h-5 w-40 bg-muted rounded animate-pulse" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-4 p-3 rounded-lg border animate-pulse">
              <div className="h-10 w-10 bg-muted rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-32 bg-muted rounded" />
                <div className="h-3 w-24 bg-muted rounded" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn("h-[400px]", className)}>
        <CardContent className="h-full flex items-center justify-center">
          <WidgetErrorFallback title="Upcoming Bills" error={error.message} onRetry={refetch} />
        </CardContent>
      </Card>
    );
  }

  const recurring = recurringTransactions || [];
  const activeRecurring = recurring.filter((r: RecurringTransaction) => r.is_active);
  
  const activeLoans = (loans || []).filter((l: Loan) => l.status === "active");

  // Combine and sort by next due date
  const allBills = [
    ...activeRecurring.map((r: RecurringTransaction) => ({
      id: `recurring-${r.id}`,
      name: r.description,
      amount: r.amount_paise,
      type: r.type,
      nextDue: r.next_due_date ? new Date(r.next_due_date) : null,
      category: r.category || "Other",
      icon: CreditCard,
    })),
    ...activeLoans.map((l: Loan) => ({
      id: `loan-${l.id}`,
      name: `${l.lender || "Loan"} EMI`,
      amount: l.emi_paise || 0,
      type: "debit" as const,
      nextDue: l.next_emi_date ? new Date(l.next_emi_date) : null,
      category: "Loan",
      icon: Home,
    })),
  ].filter((b) => b.nextDue && !isNaN(b.nextDue.getTime()))
   .sort((a, b) => (a.nextDue?.getTime() || 0) - (b.nextDue?.getTime() || 0));

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const getDaysUntil = (date: Date) => {
    const diff = Math.ceil((date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const getStatusBadge = (days: number) => {
    if (days < 0) return <Badge variant="destructive">Overdue</Badge>;
    if (days === 0) return <Badge className="bg-amber-500">Due Today</Badge>;
    if (days <= 3) return <Badge className="bg-amber-500/80">Due in {days} days</Badge>;
    return <Badge variant="secondary">Due in {days} days</Badge>;
  };

  return (
    <Card className={cn("h-[400px]", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <Bell className="h-4 w-4" />
          Upcoming Bills & Payments
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[320px]">
          <div className="space-y-3 pr-4">
            {allBills.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No upcoming bills</p>
            ) : (
              allBills.map((bill) => {
                const daysUntil = bill.nextDue ? getDaysUntil(bill.nextDue) : 0;
                const Icon = bill.icon;
                
                return (
                  <div
                    key={bill.id}
                    className={cn(
                      "flex items-center gap-4 p-3 rounded-lg border transition-colors",
                      daysUntil < 0 ? "bg-red-50 dark:bg-red-950/20" :
                      daysUntil <= 3 ? "bg-amber-50 dark:bg-amber-950/20" :
                      "hover:bg-muted/50"
                    )}
                  >
                    <div className={cn(
                      "p-2 rounded-full",
                      daysUntil < 0 ? "bg-red-100 text-red-600" :
                      daysUntil <= 3 ? "bg-amber-100 text-amber-600" :
                      "bg-blue-100 text-blue-600"
                    )}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{bill.name}</p>
                      <p className="text-xs text-muted-foreground capitalize">
                        {bill.category} • {bill.nextDue?.toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={cn(
                        "font-semibold",
                        bill.type === "credit" ? "text-green-600" : "text-red-600"
                      )}>
                        {bill.type === "credit" ? "+" : "-"}{formatPaise(bill.amount)}
                      </p>
                      {getStatusBadge(daysUntil)}
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
