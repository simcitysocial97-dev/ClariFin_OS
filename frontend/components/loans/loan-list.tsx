"use client";

/**
 * Loan List Component
 * ===================
 *
 * Table displaying all loans with summary statistics.
 * Each row is clickable to view loan details.
 */

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Pencil, Trash2, Landmark } from "lucide-react";
import { formatPaise, formatPercent } from "@/lib/format";
import type { Loan } from "@/lib/api/client";

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

interface LoanListProps {
  loans: Loan[];
  onLoanClick: (loan: Loan) => void;
  onEdit: (loan: Loan) => void;
  onDelete: (loan: Loan) => void;
}

export function LoanList({ loans, onLoanClick, onEdit, onDelete }: LoanListProps) {
  if (loans.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <Landmark className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-medium mb-2">No Loans Yet</h3>
          <p className="text-muted-foreground">
            Add your first loan to track payments and view amortization schedules.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Loan Name</TableHead>
                <TableHead>Lender</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">EMI</TableHead>
                <TableHead className="text-right">Interest Rate</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loans.map((loan) => (
                <TableRow
                  key={loan.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onLoanClick(loan)}
                >
                  <TableCell>
                    <div>
                      <p className="font-medium">{loan.name}</p>
                      {loan.tenure_months && (
                        <p className="text-xs text-muted-foreground">
                          {loan.tenure_months} months
                        </p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {loan.lender || "—"}
                  </TableCell>
                  <TableCell>
                    <Badge className={LOAN_TYPE_COLORS[loan.loan_type] || LOAN_TYPE_COLORS.other}>
                      {LOAN_TYPE_LABELS[loan.loan_type] || loan.loan_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatPaise(loan.outstanding_paise)}
                  </TableCell>
                  <TableCell className="text-right">
                    {loan.emi_paise ? formatPaise(loan.emi_paise) : "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatPercent(loan.interest_rate / 100)}
                  </TableCell>
                  <TableCell>
                    <Badge className={STATUS_COLORS[loan.status] || STATUS_COLORS.active}>
                      {loan.status.charAt(0).toUpperCase() + loan.status.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          onEdit(loan);
                        }}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(loan);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
