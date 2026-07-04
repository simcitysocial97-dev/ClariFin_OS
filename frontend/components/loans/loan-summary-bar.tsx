"use client";

/**
 * Loan Summary Bar
 * ================
 *
 * Top summary cards showing:
 * - Total outstanding across all active loans
 * - Total monthly EMI
 * - Number of active loans
 */

import { Card, CardContent } from "@/components/ui/card";
import { formatPaise } from "@/lib/format";
import { Landmark, Wallet, Activity } from "lucide-react";
import type { Loan } from "@/lib/api/client";

interface LoanSummaryBarProps {
  loans: Loan[];
}

export function LoanSummaryBar({ loans }: LoanSummaryBarProps) {
  // Filter active loans only
  const activeLoans = loans.filter(loan => loan.status === 'active');

  // Calculate totals
  const totalOutstanding = activeLoans.reduce((sum, loan) => sum + loan.outstanding_paise, 0);
  const totalEmi = activeLoans.reduce((sum, loan) => sum + (loan.emi_paise || 0), 0);
  const activeCount = activeLoans.length;

  // Calculate progress based on principal paid
  const totalPrincipal = activeLoans.reduce((sum, loan) => sum + loan.principal_paise, 0);
  const completionPercent = totalPrincipal > 0 
    ? Math.round(((totalPrincipal - totalOutstanding) / totalPrincipal) * 100)
    : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Total Outstanding */}
      <Card className="bg-red-500/5 border-red-500/20">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Outstanding</p>
              <p className="text-2xl font-bold text-red-600">{formatPaise(totalOutstanding)}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Across {activeCount} active {activeCount === 1 ? 'loan' : 'loans'}
              </p>
            </div>
            <div className="p-3 bg-red-500/10 rounded-full">
              <Landmark className="h-6 w-6 text-red-500" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Total Monthly EMI */}
      <Card className="bg-blue-500/5 border-blue-500/20">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Monthly EMI</p>
              <p className="text-2xl font-bold text-blue-600">{formatPaise(totalEmi)}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Per month
              </p>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-full">
              <Wallet className="h-6 w-6 text-blue-500" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress Overview */}
      <Card className="bg-green-500/5 border-green-500/20">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Overall Progress</p>
              <p className="text-2xl font-bold text-green-600">
                {completionPercent}%
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Principal repaid across all loans
              </p>
            </div>
            <div className="p-3 bg-green-500/10 rounded-full">
              <Activity className="h-6 w-6 text-green-500" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
