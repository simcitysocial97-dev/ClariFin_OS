"use client";

import { useState } from "react";
import {
  useRecurringTransactions,
  useCreateRecurringTransaction,
  useUpdateRecurringTransaction,
  useDeleteRecurringTransaction,
} from "@/lib/hooks/use-finance-data";
import { formatPaise } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import {
  CreditCard,
  Plus,
  Pencil,
  Trash2,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { RecurringTransactionDialog } from "./recurring-transaction-dialog";
import type { RecurringTransaction, RecurringTransactionCreate, RecurringTransactionUpdate } from "@/types/recurring";

export function SubscriptionsTable({ className }: { className?: string }) {
  const { recurringTransactions, loading, error, refetch } = useRecurringTransactions();
  const { createRecurringTransaction, creating: isCreating } = useCreateRecurringTransaction();
  const { updateRecurringTransaction, updating: isUpdating } = useUpdateRecurringTransaction();
  const { deleteRecurringTransaction, deleting: isDeleting } = useDeleteRecurringTransaction();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<RecurringTransaction | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [transactionToDelete, setTransactionToDelete] = useState<RecurringTransaction | null>(null);

  const isSubmitting = isCreating || isUpdating;

  const handleCreateClick = () => {
    setEditingTransaction(null);
    setDialogOpen(true);
  };

  const handleEditClick = (transaction: RecurringTransaction) => {
    setEditingTransaction(transaction);
    setDialogOpen(true);
  };

  const handleDeleteClick = (transaction: RecurringTransaction) => {
    setTransactionToDelete(transaction);
    setDeleteDialogOpen(true);
  };

  const handleSubmit = async (data: RecurringTransactionCreate | RecurringTransactionUpdate) => {
    try {
      if (editingTransaction) {
        await updateRecurringTransaction({ id: editingTransaction.id, transaction: data as RecurringTransactionUpdate });
      } else {
        await createRecurringTransaction(data as RecurringTransactionCreate);
      }
      setDialogOpen(false);
      refetch();
    } catch (err) {
      console.error("Failed to save recurring transaction:", err);
    }
  };

  const handleConfirmDelete = async () => {
    if (!transactionToDelete) return;
    try {
      await deleteRecurringTransaction(transactionToDelete.id);
      setDeleteDialogOpen(false);
      setTransactionToDelete(null);
      refetch();
    } catch (err) {
      console.error("Failed to delete recurring transaction:", err);
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="h-5 w-48 bg-muted rounded animate-pulse" />
            <div className="h-9 w-32 bg-muted rounded animate-pulse" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex justify-between items-center py-2">
                <div className="h-4 w-28 bg-muted rounded animate-pulse" />
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                <div className="h-4 w-24 bg-muted rounded animate-pulse" />
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
          <WidgetErrorFallback title="Subscriptions" error={error.message} onRetry={refetch} />
        </CardContent>
      </Card>
    );
  }

  const recurring = recurringTransactions || [];
  const activeRecurring = recurring.filter((r: RecurringTransaction) => r.is_active);

  return (
    <>
      <Card className={className}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              All Subscriptions & Recurring Payments
            </CardTitle>
            <Button size="sm" onClick={handleCreateClick}>
              <Plus className="h-4 w-4 mr-1" />
              Add Recurring
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {activeRecurring.length === 0 ? (
            <div className="text-center py-12">
              <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <CreditCard className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">No recurring transactions</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Add your subscriptions and recurring payments
              </p>
              <Button onClick={handleCreateClick}>
                <Plus className="h-4 w-4 mr-1" />
                Add Your First Recurring
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Next Due</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeRecurring.map((item: RecurringTransaction) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.description}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {item.category || "Other"}
                      </Badge>
                    </TableCell>
                    <TableCell className={cn(
                      "text-right font-medium",
                      item.type === "credit" ? "text-green-600" : "text-red-600"
                    )}>
                      {item.type === "credit" ? "+" : "-"}{formatPaise(item.amount_paise)}
                    </TableCell>
                    <TableCell className="capitalize">{item.frequency}</TableCell>
                    <TableCell>
                      {item.next_due_date 
                        ? new Date(item.next_due_date).toLocaleDateString() 
                        : <span className="text-muted-foreground italic">date unavailable</span>
                      }
                    </TableCell>
                    <TableCell>
                      <Badge className={item.type === "credit" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                        {item.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => handleEditClick(item)}
                          aria-label={`Edit ${item.description}`}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDeleteClick(item)}
                          disabled={isDeleting}
                          aria-label={`Delete ${item.description}`}
                        >
                          {isDeleting && transactionToDelete?.id === item.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <RecurringTransactionDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        transaction={editingTransaction}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      />

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Recurring Transaction</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{transactionToDelete?.description}</strong>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button onClick={handleConfirmDelete} disabled={isDeleting} className="bg-red-600 hover:bg-red-700">
              {isDeleting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Deleting...</> : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
