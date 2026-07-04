"use client";

/**
 * Prepayment Simulator Component
 * ==============================
 *
 * Calculate the impact of making extra prepayments on a loan.
 * Shows interest saved, months saved, and effective annual return.
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Calculator, TrendingDown, Clock, PiggyBank, Percent } from "lucide-react";
import { formatPaise, formatDate, formatPercent } from "@/lib/format";
import type { PrepaymentResult } from "@/types/loan";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface PrepaymentSimulatorProps {
  onSimulate: (data: {
    extra_payment_paise: number;
    extra_payment_date: string;
    strategy: "REDUCE_TENURE" | "REDUCE_EMI";
  }) => Promise<PrepaymentResult | null>;
  simulating: boolean;
}

export function PrepaymentSimulator({
  onSimulate,
  simulating,
}: PrepaymentSimulatorProps) {
  const [result, setResult] = useState<PrepaymentResult | null>(null);
  const [formData, setFormData] = useState({
    amount: "",
    month: "1",
    strategy: "REDUCE_TENURE" as "REDUCE_TENURE" | "REDUCE_EMI",
  });

  const handleCalculate = async () => {
    const amountPaise = Math.round(parseFloat(formData.amount || "0") * 100);
    
    // Calculate the date for the prepayment (start of next month + months)
    const today = new Date();
    const targetDate = new Date(today.getFullYear(), today.getMonth() + parseInt(formData.month), 1);
    
    const simulationResult = await onSimulate({
      extra_payment_paise: amountPaise,
      extra_payment_date: targetDate.toISOString().split("T")[0]!,
      strategy: formData.strategy,
    });
    
    if (simulationResult) {
      setResult(simulationResult);
    }
  };

  // Chart data for interest comparison
  const chartData = result
    ? [
        {
          name: "Original",
          interest: result.original_future_interest_paise / 100,
        },
        {
          name: "With Prepayment",
          interest: result.new_future_interest_paise / 100,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Calculator className="h-5 w-5" />
            Prepayment Calculator
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="prepayment-amount">Extra Payment Amount (₹)</Label>
              <Input
                id="prepayment-amount"
                type="number"
                step="0.01"
                value={formData.amount}
                onChange={(e) =>
                  setFormData({ ...formData, amount: e.target.value })
                }
                placeholder="e.g., 100000"
              />
            </div>
            <div>
              <Label htmlFor="apply-month">Apply at Month (from now)</Label>
              <Input
                id="apply-month"
                type="number"
                min="1"
                value={formData.month}
                onChange={(e) =>
                  setFormData({ ...formData, month: e.target.value })
                }
                placeholder="1"
              />
            </div>
          </div>

          <div>
            <Label className="mb-3 block">Prepayment Strategy</Label>
            <RadioGroup
              value={formData.strategy}
              onValueChange={(value: "REDUCE_TENURE" | "REDUCE_EMI") =>
                setFormData({ ...formData, strategy: value })
              }
              className="flex flex-col space-y-2"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="REDUCE_TENURE" id="reduce-tenure" />
                <Label htmlFor="reduce-tenure" className="cursor-pointer">
                  <span className="font-medium">Reduce Tenure</span>
                  <span className="text-muted-foreground text-sm ml-2">
                    Keep EMI same, pay off loan faster
                  </span>
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="REDUCE_EMI" id="reduce-emi" />
                <Label htmlFor="reduce-emi" className="cursor-pointer">
                  <span className="font-medium">Reduce EMI</span>
                  <span className="text-muted-foreground text-sm ml-2">
                    Lower monthly payments, same tenure
                  </span>
                </Label>
              </div>
            </RadioGroup>
          </div>

          <Button
            onClick={handleCalculate}
            disabled={simulating || !formData.amount}
            className="w-full"
          >
            {simulating ? "Calculating..." : "Calculate Impact"}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <Alert className="bg-green-50 border-green-200">
            <TrendingDown className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              You will save <strong>{formatPaise(result.interest_saved_paise)}</strong> in interest
              and close your loan <strong>{result.months_saved} months</strong> earlier!
            </AlertDescription>
          </Alert>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <PiggyBank className="h-4 w-4 text-green-500" />
                  <span className="text-sm text-muted-foreground">Interest Saved</span>
                </div>
                <p className="text-xl font-bold text-green-600 mt-1">
                  {formatPaise(result.interest_saved_paise)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-500" />
                  <span className="text-sm text-muted-foreground">Months Saved</span>
                </div>
                <p className="text-xl font-bold text-blue-600 mt-1">
                  {result.months_saved}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Calculator className="h-4 w-4 text-purple-500" />
                  <span className="text-sm text-muted-foreground">New Closure Date</span>
                </div>
                <p className="text-lg font-bold text-purple-600 mt-1">
                  {formatDate(result.new_closure_date)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Percent className="h-4 w-4 text-orange-500" />
                  <span className="text-sm text-muted-foreground">Effective Return</span>
                </div>
                <p className="text-xl font-bold text-orange-600 mt-1">
                  {formatPercent(result.effective_annual_return_percent / 100)}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Interest Comparison Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Interest Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    margin={{
                      top: 5,
                      right: 30,
                      left: 20,
                      bottom: 5,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="name" />
                    <YAxis
                      tickFormatter={(value) => `₹${(value / 100000).toFixed(1)}L`}
                    />
                    <Tooltip
                      formatter={(value: number) => formatPaise(value * 100)}
                    />
                    <Bar
                      dataKey="interest"
                      name="Future Interest"
                      fill="#3b82f6"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
