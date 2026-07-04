"use client";

/**
 * Amortization Table Component
 * ============================
 *
 * Displays the loan amortization schedule in a table format.
 * Highlights the current month's row.
 */

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatPaise, formatDate } from "@/lib/format";
import type { AmortizationEntry } from "@/types/loan";

interface AmortizationTableProps {
  schedule: AmortizationEntry[];
}

export function AmortizationTable({ schedule }: AmortizationTableProps) {
  // Get current date for highlighting current month
  const today = new Date();
  const currentMonth = today.getMonth();
  const currentYear = today.getFullYear();

  // Check if a period is the current month
  const isCurrentMonth = (emiDate: string): boolean => {
    const date = new Date(emiDate);
    return date.getMonth() === currentMonth && date.getFullYear() === currentYear;
  };

  if (schedule.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No amortization schedule available.
      </div>
    );
  }

  return (
    <ScrollArea className="h-[400px]">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">Month</TableHead>
            <TableHead>EMI Date</TableHead>
            <TableHead className="text-right">EMI</TableHead>
            <TableHead className="text-right">Principal</TableHead>
            <TableHead className="text-right">Interest</TableHead>
            <TableHead className="text-right">Remaining</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {schedule.map((entry) => {
            const isCurrent = isCurrentMonth(entry.emi_date);
            return (
              <TableRow
                key={entry.period}
                className={isCurrent ? "bg-primary/10 font-medium" : ""}
              >
                <TableCell>{entry.period}</TableCell>
                <TableCell>
                  {formatDate(entry.emi_date)}
                  {isCurrent && (
                    <span className="ml-2 text-xs text-primary">(Current)</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {formatPaise(entry.emi_paise)}
                </TableCell>
                <TableCell className="text-right">
                  {formatPaise(entry.principal_paise)}
                </TableCell>
                <TableCell className="text-right">
                  {formatPaise(entry.interest_paise)}
                </TableCell>
                <TableCell className="text-right">
                  {formatPaise(entry.remaining_principal_paise)}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </ScrollArea>
  );
}
