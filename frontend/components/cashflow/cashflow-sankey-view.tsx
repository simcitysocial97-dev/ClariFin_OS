"use client";

/**
 * Cash Flow Sankey View (Optional)
 * ================================
 *
 * A Sankey diagram visualization showing the flow of money from
 * income sources through to expenses and savings.
 *
 * Planned data flow:
 * - Income Sources → [Salary, Investments, Side Income, etc.]
 * - Intermediate Nodes → [Gross Income, Taxes, Net Income]
 * - Expense Categories → [Housing, Food, Transport, etc.]
 * - Savings Destinations → [Emergency Fund, Investments, Goals]
 *
 * This view is not yet implemented. The existing bar chart visualization
 * in CashflowChart provides the same data in a different format.
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { GitBranch } from "lucide-react";

interface CashflowSankeyViewProps {
  className?: string;
}

export function CashflowSankeyView({ className }: CashflowSankeyViewProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2 text-muted-foreground">
          <GitBranch className="h-4 w-4" />
          Sankey view (optional)
        </CardTitle>
        <CardDescription className="text-xs">
          Visual flow of money from sources to destinations
        </CardDescription>
      </CardHeader>
      <CardContent className="h-[200px] flex flex-col items-center justify-center text-center space-y-3">
        <div className="p-3 rounded-full bg-muted">
          <GitBranch className="h-6 w-6 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">
            Not implemented yet
          </p>
          <p className="text-xs text-muted-foreground max-w-[280px]">
            Will show money flow: Income Sources → Net Income → Expenses & Savings
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
