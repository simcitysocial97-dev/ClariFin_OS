"use client";

/**
 * Portfolio Summary Component
 * ===========================
 *
 * Top section showing:
 * - Total Invested
 * - Current Value
 * - Total Gain/Loss (with color coding)
 */

import { Card, CardContent } from "@/components/ui/card";
import { formatPaise, formatPercent } from "@/lib/format";
import { TrendingUp, TrendingDown, Wallet, PiggyBank } from "lucide-react";
import type { InvestmentSummary } from "@/lib/api/client";

interface PortfolioSummaryProps {
  summary: InvestmentSummary | null;
}

export function PortfolioSummary({ summary }: PortfolioSummaryProps) {
  if (!summary) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4">
              <div className="h-16 bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const totalInvested = summary.total_invested_paise;
  const currentValue = summary.total_current_value_paise;
  const totalGain = summary.total_gain_loss_paise;
  const gainPercent = summary.gain_loss_percent;
  const isPositive = totalGain >= 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Total Invested */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Invested</p>
              <p className="text-2xl font-bold">{formatPaise(totalInvested)}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {summary.count} active investments
              </p>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-full">
              <PiggyBank className="h-6 w-6 text-blue-500" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Value */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Current Value</p>
              <p className="text-2xl font-bold">{formatPaise(currentValue)}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Latest market value
              </p>
            </div>
            <div className="p-3 bg-purple-500/10 rounded-full">
              <Wallet className="h-6 w-6 text-purple-500" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Total Gain/Loss */}
      <Card className={isPositive ? "bg-green-500/5 border-green-500/20" : "bg-red-500/5 border-red-500/20"}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Gain/Loss</p>
              <p className={`text-2xl font-bold ${isPositive ? "text-green-600" : "text-red-600"}`}>
                {isPositive ? "+" : ""}{formatPaise(totalGain)}
              </p>
              <div className="flex items-center gap-1 mt-1">
                {isPositive ? (
                  <TrendingUp className="h-3 w-3 text-green-500" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-red-500" />
                )}
                <span className={`text-xs ${isPositive ? "text-green-600" : "text-red-600"}`}>
                  {isPositive ? "+" : ""}{formatPercent(gainPercent / 100)}
                </span>
              </div>
            </div>
            <div className={`p-3 rounded-full ${isPositive ? "bg-green-500/10" : "bg-red-500/10"}`}>
              {isPositive ? (
                <TrendingUp className="h-6 w-6 text-green-500" />
              ) : (
                <TrendingDown className="h-6 w-6 text-red-500" />
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
