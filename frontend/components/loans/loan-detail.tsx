"use client";

/**
 * Loan Detail Component
 * =====================
 *
 * Comprehensive loan detail view with tabs for:
 * - Overview: Loan details, progress, summary
 * - Amortization Schedule: Table and chart
 * - Payment History: Recorded payments
 * - Prepayment Simulator: Calculate prepayment impact
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Landmark, Calendar, Wallet, Percent, CheckCircle, Clock } from "lucide-react";
import { AmortizationTable } from "./amortization-table";
import { AmortizationChart } from "./amortization-chart";
import { PaymentHistory } from "./payment-history";
import { PrepaymentSimulator } from "./prepayment-simulator";
import { formatPaise, formatDate, formatPercent, formatTenure } from "@/lib/format";
import type { Loan, LoanSummary, AmortizationSchedule, LoanPayment, PrepaymentResult } from "@/types/loan";

// Loan type labels and colors
const LOAN_TYPE_LABELS: Record<string, string> = {
  home: "Home Loan",
  car: "Car Loan",
  personal: "Personal Loan",
  education: "Education Loan",
  credit_card: "Credit Card",
  gold: "Gold Loan",
  other: "Other",
};

const LOAN_TYPE_COLORS: Record<string, string> = {
  home: "bg-emerald-100 text-emerald-800",
  car: "bg-blue-100 text-blue-800",
  personal: "bg-purple-100 text-purple-800",
  education: "bg-indigo-100 text-indigo-800",
  credit_card: "bg-orange-100 text-orange-800",
  gold: "bg-yellow-100 text-yellow-800",
  other: "bg-gray-100 text-gray-800",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  closed: "bg-gray-100 text-gray-800",
  defaulted: "bg-red-100 text-red-800",
};

interface LoanDetailProps {
  loan: Loan;
  summary: LoanSummary | null;
  summaryLoading: boolean;
  amortization: AmortizationSchedule | null;
  amortizationLoading: boolean;
  payments: LoanPayment[];
  paymentsLoading: boolean;
  onRecordPayment: (payment: {
    principal_component_paise: number;
    interest_component_paise: number;
    payment_date: string;
    remaining_principal_paise: number;
  }) => void;
  onSimulatePrepayment: (data: {
    extra_payment_paise: number;
    extra_payment_date: string;
    strategy: "REDUCE_TENURE" | "REDUCE_EMI";
  }) => Promise<PrepaymentResult | null>;
  simulatingPrepayment: boolean;
}

export function LoanDetail({
  loan,
  summary,
  summaryLoading,
  amortization,
  amortizationLoading,
  payments,
  paymentsLoading,
  onRecordPayment,
  onSimulatePrepayment,
  simulatingPrepayment,
}: LoanDetailProps) {
  const [activeTab, setActiveTab] = useState("overview");

  // Calculate progress percentage
  const progressPercent =
    loan.principal_paise > 0
      ? Math.round(
          ((loan.principal_paise - loan.outstanding_paise) / loan.principal_paise) * 100
        )
      : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold">{loan.name}</h2>
            <Badge className={STATUS_COLORS[loan.status] || STATUS_COLORS.active}>
              {loan.status.charAt(0).toUpperCase() + loan.status.slice(1)}
            </Badge>
          </div>
          <p className="text-muted-foreground">
            {loan.lender || "No lender specified"} · {" "}
            <Badge variant="outline" className={LOAN_TYPE_COLORS[loan.loan_type]}>
              {LOAN_TYPE_LABELS[loan.loan_type] || loan.loan_type}
            </Badge>
          </p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="amortization">Amortization</TabsTrigger>
          <TabsTrigger value="payments">Payments</TabsTrigger>
          <TabsTrigger value="prepayment">Prepayment</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {/* Progress Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Loan Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Principal Repaid</span>
                <span className="font-medium">{progressPercent}%</span>
              </div>
              <Progress value={progressPercent} className="h-2" />
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>{formatPaise(loan.principal_paise - loan.outstanding_paise)} repaid</span>
                <span>{formatPaise(loan.outstanding_paise)} remaining</span>
              </div>
            </CardContent>
          </Card>

          {/* Loan Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Landmark className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Principal</span>
                </div>
                <p className="text-xl font-bold mt-1">
                  {formatPaise(loan.principal_paise)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Wallet className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Outstanding</span>
                </div>
                <p className="text-xl font-bold text-red-600 mt-1">
                  {formatPaise(loan.outstanding_paise)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Percent className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Interest Rate</span>
                </div>
                <p className="text-xl font-bold mt-1">
                  {formatPercent(loan.interest_rate / 100)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Start Date</span>
                </div>
                <p className="text-lg font-medium mt-1">
                  {formatDate(loan.start_date)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Wallet className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Monthly EMI</span>
                </div>
                <p className="text-xl font-bold mt-1">
                  {loan.emi_paise ? formatPaise(loan.emi_paise) : "—"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Tenure</span>
                </div>
                <p className="text-xl font-bold mt-1">
                  {loan.tenure_months ? formatTenure(loan.tenure_months) : "—"}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Summary from API */}
          {summaryLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          ) : summary ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm text-muted-foreground">Completion</span>
                  </div>
                  <p className="text-2xl font-bold text-green-600 mt-1">
                    {summary.completion_percent.toFixed(1)}%
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-blue-500" />
                    <span className="text-sm text-muted-foreground">Projected Closure</span>
                  </div>
                  <p className="text-xl font-bold text-blue-600 mt-1">
                    {formatDate(summary.projected_closure_date)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {summary.days_to_close > 0
                      ? `${summary.days_to_close} days remaining`
                      : "Loan closed"}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-purple-500" />
                    <span className="text-sm text-muted-foreground">Months Remaining</span>
                  </div>
                  <p className="text-2xl font-bold text-purple-600 mt-1">
                    {summary.months_remaining}
                  </p>
                </CardContent>
              </Card>
            </div>
          ) : null}
        </TabsContent>

        {/* Amortization Tab */}
        <TabsContent value="amortization" className="space-y-4">
          {amortizationLoading ? (
            <Skeleton className="h-[400px]" />
          ) : amortization ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-muted-foreground">Total EMI</p>
                    <p className="text-xl font-bold mt-1">
                      {formatPaise(amortization.emi_paise)}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-muted-foreground">Total Periods</p>
                    <p className="text-xl font-bold mt-1">
                      {amortization.total_periods}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-muted-foreground">Total Interest</p>
                    <p className="text-xl font-bold text-amber-600 mt-1">
                      {formatPaise(amortization.total_interest_paise)}
                    </p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Principal vs Interest Over Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <AmortizationChart schedule={amortization.schedule} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Amortization Schedule</CardTitle>
                </CardHeader>
                <CardContent>
                  <AmortizationTable schedule={amortization.schedule} />
                </CardContent>
              </Card>
            </>
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>No Schedule Available</AlertTitle>
              <AlertDescription>
                Could not load amortization schedule. Please check loan details.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Payments Tab */}
        <TabsContent value="payments">
          {paymentsLoading ? (
            <Skeleton className="h-[300px]" />
          ) : (
            <PaymentHistory
              payments={payments}
              onRecordPayment={onRecordPayment}
            />
          )}
        </TabsContent>

        {/* Prepayment Tab */}
        <TabsContent value="prepayment">
          <PrepaymentSimulator
            onSimulate={onSimulatePrepayment}
            simulating={simulatingPrepayment}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
