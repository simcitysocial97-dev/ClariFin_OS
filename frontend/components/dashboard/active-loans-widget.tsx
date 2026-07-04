"use client";

/**
 * Active Loans Widget
 * ===================
 * 
 * Compact list showing active loans with outstanding balance and EMI.
 * Links to /loans page for full details.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useLoansQuery } from "@/lib/hooks/use-query-finance";
import { formatPaise } from "@/lib/format";
import { ListWidgetSkeleton } from "./skeletons";
import { WidgetErrorFallback } from "./widget-error-fallback";
import { Landmark, ArrowRight } from "lucide-react";
import Link from "next/link";

interface ActiveLoansWidgetProps {
  mode?: "personal" | "family";
}

interface Loan {
  id: number;
  name: string;
  outstanding_paise: number;
  emi_paise: number;
  interest_rate: number;
  status: string;
}

export function ActiveLoansWidget({ mode = "personal" }: ActiveLoansWidgetProps) {
  const { data, loading, error, refetch } = useLoansQuery();

  if (loading) {
    return <ListWidgetSkeleton />;
  }

  if (error) {
    return (
      <WidgetErrorFallback
        title="Active Loans"
        error={error.message}
        onRetry={refetch}
      />
    );
  }

  // Filter active loans
  const activeLoans: Loan[] = (data?.loans || [])
    .filter((loan: Loan) => loan.status === "active")
    .slice(0, 10);

  // Empty state
  if (activeLoans.length === 0) {
    return (
      <Card className="h-[320px]">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Active Loans</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[250px] text-center px-6">
          <Landmark className="h-10 w-10 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground text-sm">No active loans</p>
          <p className="text-muted-foreground text-xs mt-1">
            Add loans to track your EMIs and outstanding balance
          </p>
          <Link href="/loans" className="mt-4">
            <Button variant="outline" size="sm">
              View Loans
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Active Loans
          {mode === "family" && <span className="text-muted-foreground ml-2">· Family</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[200px] px-6">
          <div className="space-y-3 py-2">
            {activeLoans.map((loan) => (
              <div
                key={loan.id}
                className="flex items-center justify-between py-2 border-b border-border/50 last:border-0"
              >
                <div className="flex-1 min-w-0 mr-3">
                  <p className="text-sm font-medium truncate">{loan.name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <p className="text-xs text-muted-foreground">
                      EMI: {formatPaise(loan.emi_paise)}
                    </p>
                    <Badge variant="outline" className="text-[10px] px-1 py-0">
                      {loan.interest_rate.toFixed(1)}%
                    </Badge>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-mono font-medium">
                    {formatPaise(loan.outstanding_paise)}
                  </p>
                  <p className="text-[10px] text-muted-foreground">outstanding</p>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="px-6 pb-4 pt-2">
          <Link href="/loans">
            <Button variant="ghost" size="sm" className="w-full">
              View all loans
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
