"use client";

/**
 * Payment History Component
 * =========================
 *
 * Displays loan payment history with a table.
 * Includes a form to record new payments.
 */

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, Receipt } from "lucide-react";
import { formatPaise, formatDate } from "@/lib/format";
import type { LoanPayment } from "@/types/loan";

interface PaymentHistoryProps {
  payments: LoanPayment[];
  onRecordPayment: (payment: {
    principal_component_paise: number;
    interest_component_paise: number;
    payment_date: string;
    remaining_principal_paise: number;
  }) => void;
}

export function PaymentHistory({ payments, onRecordPayment }: PaymentHistoryProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<{
    principal: string;
    interest: string;
    payment_date: string;
    remaining: string;
  }>({
    principal: "",
    interest: "",
    payment_date: new Date().toISOString().split("T")[0] || "",
    remaining: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRecordPayment({
      principal_component_paise: Math.round(parseFloat(formData.principal || "0") * 100),
      interest_component_paise: Math.round(parseFloat(formData.interest || "0") * 100),
      payment_date: formData.payment_date,
      remaining_principal_paise: Math.round(parseFloat(formData.remaining || "0") * 100),
    });
    setDialogOpen(false);
    setFormData({
      principal: "",
      interest: "",
      payment_date: new Date().toISOString().split("T")[0] || "",
      remaining: "",
    });
  };

  // Sort payments by date (newest first)
  const sortedPayments = [...payments].sort(
    (a, b) => new Date(b.payment_date).getTime() - new Date(a.payment_date).getTime()
  );

  return (
    <div className="space-y-4">
      {/* Header with Record Payment button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Payment History</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Record Payment
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Record Payment</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 pt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="principal">Principal Component (₹)</Label>
                  <Input
                    id="principal"
                    type="number"
                    step="0.01"
                    value={formData.principal}
                    onChange={(e) =>
                      setFormData({ ...formData, principal: e.target.value })
                    }
                    placeholder="0.00"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="interest">Interest Component (₹)</Label>
                  <Input
                    id="interest"
                    type="number"
                    step="0.01"
                    value={formData.interest}
                    onChange={(e) =>
                      setFormData({ ...formData, interest: e.target.value })
                    }
                    placeholder="0.00"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="payment_date">Payment Date</Label>
                  <Input
                    id="payment_date"
                    type="date"
                    value={formData.payment_date}
                    onChange={(e) =>
                      setFormData({ ...formData, payment_date: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="remaining">Remaining Principal (₹)</Label>
                  <Input
                    id="remaining"
                    type="number"
                    step="0.01"
                    value={formData.remaining}
                    onChange={(e) =>
                      setFormData({ ...formData, remaining: e.target.value })
                    }
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2 pt-4">
                <Button type="submit" className="flex-1">
                  Record Payment
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Payments Table */}
      {sortedPayments.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Receipt className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">No Payments Recorded</h3>
            <p className="text-muted-foreground">
              Record your first payment to start tracking loan progress.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Principal</TableHead>
                    <TableHead className="text-right">Interest</TableHead>
                    <TableHead className="text-right">Remaining</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedPayments.map((payment) => {
                    const totalAmount =
                      payment.principal_component_paise +
                      payment.interest_component_paise;
                    return (
                      <TableRow key={payment.id}>
                        <TableCell>{formatDate(payment.payment_date)}</TableCell>
                        <TableCell className="text-right font-medium">
                          {formatPaise(totalAmount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatPaise(payment.principal_component_paise)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatPaise(payment.interest_component_paise)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatPaise(payment.remaining_principal_paise)}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
