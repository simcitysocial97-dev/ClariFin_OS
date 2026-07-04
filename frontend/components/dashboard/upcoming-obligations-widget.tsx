"use client";

/**
 * Upcoming Obligations Widget
 * ===========================
 * 
 * Shows next 5 upcoming items combined from:
 * - Active loans (EMI payments)
 * - Active recurring transactions (subscriptions/SIPs)
 * 
 * Displays: name, amount, due date (if available), type badge
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useLoansQuery, useRecurringTransactionsQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise } from "@/lib/format";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Calendar, Wallet, Repeat, Landmark, ArrowRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import type { Loan } from "@/types/loan";
import type { RecurringTransaction } from "@/types/recurring";

interface UpcomingObligationsWidgetProps {
  mode?: "personal" | "family";
}

// Combined obligation type
type Obligation = 
  | { type: 'loan'; data: Loan }
  | { type: 'recurring'; data: RecurringTransaction };

function getBadgeForObligation(item: Obligation) {
  if (item.type === 'loan') {
    return { label: 'Loan', variant: 'default' as const, icon: Landmark };
  }
  
  const category = item.data.category.toLowerCase();
  if (category.includes('sip')) {
    return { label: 'SIP', variant: 'secondary' as const, icon: Wallet };
  }
  if (category.includes('subscription') || category.includes('membership')) {
    return { label: 'Subscription', variant: 'outline' as const, icon: Repeat };
  }
  if (category.includes('emi') || category.includes('loan')) {
    return { label: 'EMI', variant: 'default' as const, icon: Landmark };
  }
  return { label: 'Recurring', variant: 'secondary' as const, icon: Repeat };
}

function formatDueDate(dateString: string | null | undefined): { text: string; isOverdue: boolean } {
  if (!dateString) {
    return { text: 'Due date unavailable', isOverdue: false };
  }
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return { text: `${Math.abs(diffDays)}d overdue`, isOverdue: true };
    }
    if (diffDays === 0) {
      return { text: 'Due today', isOverdue: false };
    }
    if (diffDays === 1) {
      return { text: 'Tomorrow', isOverdue: false };
    }
    if (diffDays <= 7) {
      return { text: `${diffDays} days`, isOverdue: false };
    }
    
    return { text: date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }), isOverdue: false };
  } catch {
    return { text: 'Invalid date', isOverdue: false };
  }
}

function ObligationRow({ item }: { item: Obligation }) {
  const badge = getBadgeForObligation(item);
  const BadgeIcon = badge.icon;
  
  const name = item.type === 'loan' ? item.data.name : item.data.description;
  const amount = item.type === 'loan' ? item.data.emi_paise : item.data.amount_paise;
  const dueDate = item.type === 'loan' ? item.data.next_emi_date : item.data.next_due_date;
  
  const dateInfo = formatDueDate(dueDate);
  
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border/50 last:border-0">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <Badge variant={badge.variant} className="shrink-0 flex items-center gap-1 text-[10px] px-1.5 py-0.5">
          <BadgeIcon className="h-3 w-3" />
          {badge.label}
        </Badge>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium truncate" title={name}>
            {name}
          </p>
          <p className={cn("text-xs", dateInfo.isOverdue ? "text-red-500 font-medium" : "text-muted-foreground")}>
            {dateInfo.text}
          </p>
        </div>
      </div>
      <p className="text-sm font-semibold shrink-0 ml-2">
        {formatPaise(amount)}
      </p>
    </div>
  );
}

function UpcomingObligationsSkeleton() {
  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-40" />
      </CardHeader>
      <CardContent className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3 flex-1">
              <Skeleton className="h-5 w-16" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
            <Skeleton className="h-4 w-20" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function UpcomingObligationsWidget({ mode = "personal" }: UpcomingObligationsWidgetProps) {
  const { 
    data: loansData, 
    loading: loansLoading, 
    error: loansError, 
    refetch: refetchLoans 
  } = useLoansQuery();
  
  const { 
    data: recurringData, 
    loading: recurringLoading, 
    error: recurringError, 
    refetch: refetchRecurring 
  } = useRecurringTransactionsQuery();

  const loading = loansLoading || recurringLoading;
  const error = loansError || recurringError;

  const handleRetry = () => {
    refetchLoans();
    refetchRecurring();
  };

  if (loading) {
    return <UpcomingObligationsSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Upcoming Obligations"
        error={error.message}
        onRetry={handleRetry}
      />
    );
  }

  // Filter and combine obligations
  const activeLoans: Obligation[] = (loansData?.loans || [])
    .filter(loan => loan.status === 'active')
    .map(loan => ({ type: 'loan', data: loan }));

  const activeRecurring: Obligation[] = (recurringData?.recurring || [])
    .filter(rec => rec.is_active && rec.type === 'debit') // Only debit recurring (expenses)
    .map(rec => ({ type: 'recurring', data: rec }));

  const allObligations = [...activeLoans, ...activeRecurring];

  // Sort: items with due dates first (sorted by date), then items without dates
  const sortedObligations = allObligations.sort((a, b) => {
    const dateA = a.type === 'loan' ? a.data.next_emi_date : a.data.next_due_date;
    const dateB = b.type === 'loan' ? b.data.next_emi_date : b.data.next_due_date;
    
    // Both have dates - sort by date
    if (dateA && dateB) {
      return new Date(dateA).getTime() - new Date(dateB).getTime();
    }
    // Only A has date - A comes first
    if (dateA && !dateB) return -1;
    // Only B has date - B comes first
    if (!dateA && dateB) return 1;
    // Neither has date - keep original order
    return 0;
  });

  // Take top 5
  const topObligations = sortedObligations.slice(0, 5);

  // Empty state
  if (topObligations.length === 0) {
    return (
      <Card className="h-[280px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">
            Upcoming Obligations
            {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[200px] text-center">
          <Calendar className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No upcoming obligations</p>
          <p className="text-muted-foreground text-xs mt-1 mb-4">
            Add loans or recurring transactions to track payments
          </p>
          <div className="flex gap-2">
            <Link href="/loans">
              <Button variant="outline" size="sm">
                Add Loan
              </Button>
            </Link>
            <Link href="/recurring">
              <Button variant="outline" size="sm">
                Add Recurring
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[280px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Upcoming Obligations
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[200px] px-6">
          <div className="py-2">
            {topObligations.map((item) => (
              <ObligationRow key={`${item.type}-${item.type === 'loan' ? item.data.id : item.data.id}`} item={item} />
            ))}
          </div>
        </ScrollArea>
        
        {/* CTAs */}
        <div className="px-6 pb-4 pt-2 flex gap-2">
          <Link href="/recurring" className="flex-1">
            <Button variant="ghost" size="sm" className="w-full">
              View Recurring
              <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </Link>
          <Link href="/loans" className="flex-1">
            <Button variant="ghost" size="sm" className="w-full">
              View Loans
              <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
