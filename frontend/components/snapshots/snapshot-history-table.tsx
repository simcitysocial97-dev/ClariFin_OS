"use client";

import { useSnapshots } from "@/lib/hooks/use-finance-data";
import { formatPaise } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import { History, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MonthlySnapshot } from "@/types/financial";

interface SnapshotWithChanges extends MonthlySnapshot {
  change: number;
  changePercent: number;
}

export function SnapshotHistoryTable({ className }: { className?: string }) {
  const { snapshots, loading, error, refetch } = useSnapshots();
  const snapshotsList = snapshots || [];

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <div className="h-5 w-48 bg-muted rounded animate-pulse" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex justify-between items-center py-2">
                <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <WidgetErrorFallback title="Snapshot History" error={error.message} onRetry={refetch} />
        </CardContent>
      </Card>
    );
  }

  // Calculate month-over-month changes
  const snapshotsWithChanges: SnapshotWithChanges[] = snapshotsList.map((snapshot: MonthlySnapshot, index: number) => {
    const prevSnapshot = index < snapshotsList.length - 1 ? snapshotsList[index + 1] : null;
    const change = prevSnapshot 
      ? snapshot.net_worth_paise - prevSnapshot.net_worth_paise 
      : 0;
    const changePercent = prevSnapshot && prevSnapshot.net_worth_paise !== 0
      ? (change / Math.abs(prevSnapshot.net_worth_paise)) * 100
      : 0;
    return { ...snapshot, change, changePercent };
  });

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <History className="h-4 w-4" />
          Snapshot History
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Month</TableHead>
              <TableHead className="text-right">Total Assets</TableHead>
              <TableHead className="text-right">Total Liabilities</TableHead>
              <TableHead className="text-right">Net Worth</TableHead>
              <TableHead className="text-right">MoM Change</TableHead>
              <TableHead className="text-right">Savings Rate</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {snapshotsList.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                  No snapshots found. Generate your first snapshot to start tracking.
                </TableCell>
              </TableRow>
            ) : (
              snapshotsWithChanges.map((snapshot: SnapshotWithChanges) => (
                <TableRow key={snapshot.month}>
                  <TableCell className="font-medium">{snapshot.month}</TableCell>
                  <TableCell className="text-right text-green-600">
                    {formatPaise(snapshot.total_income_paise + snapshot.total_investment_paise)}
                  </TableCell>
                  <TableCell className="text-right text-red-600">
                    {formatPaise(snapshot.total_emi_paise)}
                  </TableCell>
                  <TableCell className={cn(
                    "text-right font-semibold",
                    snapshot.net_worth_paise >= 0 ? "text-green-600" : "text-red-600"
                  )}>
                    {formatPaise(snapshot.net_worth_paise)}
                  </TableCell>
                  <TableCell className="text-right">
                    {snapshot.change !== 0 ? (
                      <Badge className={cn(
                        snapshot.change > 0 ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                      )}>
                        {snapshot.change > 0 ? (
                          <TrendingUp className="h-3 w-3 mr-1 inline" />
                        ) : (
                          <TrendingDown className="h-3 w-3 mr-1 inline" />
                        )}
                        {snapshot.change > 0 ? "+" : ""}
                        {snapshot.changePercent.toFixed(1)}%
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant="outline">
                      {snapshot.savings_rate.toFixed(1)}%
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
