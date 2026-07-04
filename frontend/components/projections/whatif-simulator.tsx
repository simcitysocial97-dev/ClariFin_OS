"use client";

/**
 * What-If Simulator Component
 * ============================
 * Tab 3: Scenario builder comparing current vs modified paths
 */

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  GitCompare,
  TrendingUp,
  PiggyBank,
  Wallet,
  Calculator,
} from "lucide-react";
import { useCalculateWhatIf, useLoans } from "@/lib/hooks/use-finance-data";
import { formatPaiseCompact } from "@/lib/format";
import { ProjectionChart } from "./projection-chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function WhatIfSimulator() {
  const [increaseSavings, setIncreaseSavings] = useState("");
  const [extraLoanPayment, setExtraLoanPayment] = useState("");
  const [selectedLoanId, setSelectedLoanId] = useState<string>("");
  const [newSIP, setNewSIP] = useState("");
  const [showResults, setShowResults] = useState(false);

  const { data, loading: calculating } = useCalculateWhatIf();
  const { loans, loading: loansLoading } = useLoans();

  const handleCalculate = () => {
    setShowResults(true);
  };

  const chartData = useMemo(() => {
    if (!data?.baseline || !data?.modified) return [];

    const maxLength = Math.max(
      data.baseline.length,
      data.modified.length
    );

    return Array.from({ length: maxLength }, (_, i) => ({
      month: data.baseline[i]?.month || data.modified[i]?.month || "",
      "Current Path": data.baseline[i]?.projected_net_worth_paise || 0,
      "Modified Path": data.modified[i]?.projected_net_worth_paise || 0,
    }));
  }, [result]);

  const comparisonData = useMemo(() => {
    if (!data) return null;

    const getValueAtYear = (
      data: typeof data.baseline,
      year: number
    ): number => {
      const index = year * 12 - 1;
      return data[index]?.projected_net_worth_paise || 0;
    };

    return {
      year1: {
        baseline: getValueAtYear(data.baseline, 1),
        modified: getValueAtYear(data.modified, 1),
        diff: data.difference_at_1y_paise,
      },
      year3: {
        baseline: getValueAtYear(data.baseline, 3),
        modified: getValueAtYear(data.modified, 3),
        diff: data.difference_at_3y_paise,
      },
      year5: {
        baseline: getValueAtYear(data.baseline, 5),
        modified: getValueAtYear(data.modified, 5),
        diff: data.difference_at_5y_paise,
      },
      improvement: data.percentage_improvement_5y,
    };
  }, [result]);

  if (loansLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Scenario Builder */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="h-5 w-5" />
            Build Your Scenario
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="increase-savings" className="flex items-center gap-2">
                <PiggyBank className="h-4 w-4" />
                Increase Monthly Savings By (₹)
              </Label>
              <Input
                id="increase-savings"
                type="number"
                placeholder="5000"
                value={increaseSavings}
                onChange={(e) => setIncreaseSavings(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-sip" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Start New SIP (₹/month)
              </Label>
              <Input
                id="new-sip"
                type="number"
                placeholder="10000"
                value={newSIP}
                onChange={(e) => setNewSIP(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="extra-loan" className="flex items-center gap-2">
                <Wallet className="h-4 w-4" />
                Extra Loan Payment (₹/month)
              </Label>
              <Input
                id="extra-loan"
                type="number"
                placeholder="5000"
                value={extraLoanPayment}
                onChange={(e) => setExtraLoanPayment(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="loan-select">Select Loan (if applicable)</Label>
              <Select value={selectedLoanId} onValueChange={setSelectedLoanId}>
                <SelectTrigger id="loan-select">
                  <SelectValue placeholder="Select a loan" />
                </SelectTrigger>
                <SelectContent>
                  {loans.map((loan) => (
                    <SelectItem key={loan.id} value={String(loan.id)}>
                      {loan.name} - {loan.lender}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleCalculate}
            disabled={
              calculating ||
              (!increaseSavings && !extraLoanPayment && !newSIP)
            }
            className="w-full"
          >
            {calculating ? (
              "Calculating..."
            ) : (
              <>
                <Calculator className="h-4 w-4 mr-2" />
                Calculate Impact
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {showResults && data && comparisonData && (
        <>
          {/* Comparison Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Trajectory Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <ProjectionChart
                data={chartData}
                lines={[
                  {
                    key: "Current Path",
                    name: "Current Path",
                    color: "#6b7280",
                    type: "line",
                  },
                  {
                    key: "Modified Path",
                    name: "Modified Path",
                    color: "#22c55e",
                    type: "line",
                    strokeWidth: 3,
                  },
                ]}
                height={350}
              />
            </CardContent>
          </Card>

          {/* Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">
                  At 1 Year
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Current:</span>
                  <span>{formatPaiseCompact(comparisonData.year1.baseline)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Modified:</span>
                  <span className="font-medium">
                    {formatPaiseCompact(comparisonData.year1.modified)}
                  </span>
                </div>
                <div className="flex justify-between text-sm pt-2 border-t">
                  <span className="text-green-600 font-medium">Difference:</span>
                  <span className="font-bold text-green-600">
                    +{formatPaiseCompact(comparisonData.year1.diff)}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">
                  At 3 Years
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Current:</span>
                  <span>{formatPaiseCompact(comparisonData.year3.baseline)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Modified:</span>
                  <span className="font-medium">
                    {formatPaiseCompact(comparisonData.year3.modified)}
                  </span>
                </div>
                <div className="flex justify-between text-sm pt-2 border-t">
                  <span className="text-green-600 font-medium">Difference:</span>
                  <span className="font-bold text-green-600">
                    +{formatPaiseCompact(comparisonData.year3.diff)}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-green-500/30 bg-green-50/50 dark:bg-green-950/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">
                  At 5 Years
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Current:</span>
                  <span>{formatPaiseCompact(comparisonData.year5.baseline)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Modified:</span>
                  <span className="font-medium">
                    {formatPaiseCompact(comparisonData.year5.modified)}
                  </span>
                </div>
                <div className="flex justify-between text-sm pt-2 border-t">
                  <span className="text-green-600 font-medium">
                    Extra Growth:
                  </span>
                  <span className="font-bold text-green-600">
                    +{comparisonData.improvement.toFixed(1)}%
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Summary Impact */}
          <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg font-semibold">Total Impact at 5 Years</p>
                <p className="text-muted-foreground">
                  By making these changes, you'll have an additional
                </p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-green-600">
                  +{formatPaiseCompact(comparisonData.year5.diff)}
                </p>
                <p className="text-sm text-muted-foreground">
                  vs current path
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
