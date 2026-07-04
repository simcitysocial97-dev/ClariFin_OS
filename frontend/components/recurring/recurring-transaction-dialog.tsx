"use client";

/**
 * Recurring Transaction Dialog
 * ============================
 * Dialog for creating and editing recurring transactions.
 */

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Edit2, Loader2 } from "lucide-react";
import { rupeesToPaise } from "@/lib/format";
import type { RecurringTransaction, RecurringTransactionCreate, RecurringTransactionUpdate } from "@/types/recurring";

// ============================================================
// Constants
// ============================================================

const FREQUENCIES = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "annual", label: "Annual" },
] as const;

const TYPES = [
  { value: "debit", label: "Debit (Expense)" },
  { value: "credit", label: "Credit (Income)" },
] as const;

// ============================================================
// Types
// ============================================================

interface RecurringTransactionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transaction?: RecurringTransaction | null;
  onSubmit: (data: RecurringTransactionCreate | RecurringTransactionUpdate) => Promise<void>;
  isSubmitting?: boolean;
}

// ============================================================
// Component
// ============================================================

export function RecurringTransactionDialog({
  open,
  onOpenChange,
  transaction,
  onSubmit,
  isSubmitting = false,
}: RecurringTransactionDialogProps) {
  const isEditing = !!transaction;

  // Form state
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState<string>("");
  const [type, setType] = useState<string>("debit");
  const [category, setCategory] = useState("");
  const [frequency, setFrequency] = useState<string>("monthly");
  const [nextDueDate, setNextDueDate] = useState<string>("");
  const [isActive, setIsActive] = useState<boolean>(true);
  const [notes, setNotes] = useState<string>("");

  // Reset form when dialog opens/closes or transaction changes
  useEffect(() => {
    if (open) {
      if (transaction) {
        // Edit mode - populate form
        setDescription(transaction.description);
        setAmount((transaction.amount_paise / 100).toString());
        setType(transaction.type);
        setCategory(transaction.category || "");
        setFrequency(transaction.frequency);
        setNextDueDate(transaction.next_due_date || "");
        setIsActive(transaction.is_active);
        setNotes(transaction.notes || "");
      } else {
        // Create mode - reset form
        setDescription("");
        setAmount("");
        setType("debit");
        setCategory("");
        setFrequency("monthly");
        setNextDueDate("");
        setIsActive(true);
        setNotes("");
      }
    }
  }, [open, transaction]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const amountRupees = parseFloat(amount);
    if (isNaN(amountRupees) || amountRupees < 0) {
      return;
    }

    const baseData = {
      description,
      amount_paise: rupeesToPaise(amountRupees),
      type: type as RecurringTransaction["type"],
      category: category || "Uncategorized",
      frequency: frequency as RecurringTransaction["frequency"],
      next_due_date: nextDueDate || null,
      is_active: isActive,
      notes: notes || null,
    };

    if (isEditing && transaction) {
      // Only include changed fields for update
      const updateData: RecurringTransactionUpdate = {};
      if (description !== transaction.description) updateData.description = description;
      if (baseData.amount_paise !== transaction.amount_paise) updateData.amount_paise = baseData.amount_paise;
      if (type !== transaction.type) updateData.type = type as RecurringTransaction["type"];
      if (baseData.category !== transaction.category) updateData.category = baseData.category;
      if (frequency !== transaction.frequency) updateData.frequency = frequency as RecurringTransaction["frequency"];
      if (baseData.next_due_date !== transaction.next_due_date) updateData.next_due_date = baseData.next_due_date;
      if (isActive !== transaction.is_active) updateData.is_active = isActive;
      if (baseData.notes !== transaction.notes) updateData.notes = baseData.notes;
      
      await onSubmit(updateData);
    } else {
      await onSubmit(baseData as RecurringTransactionCreate);
    }
  };

  const isFormValid = description.trim() !== "" && amount !== "" && !isNaN(parseFloat(amount));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <Edit2 className="h-5 w-5" />
                  Edit Recurring Transaction
                </>
              ) : (
                <>
                  <Plus className="h-5 w-5" />
                  Add Recurring Transaction
                </>
              )}
            </DialogTitle>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Description */}
            <div className="grid gap-2">
              <Label htmlFor="description">
                Description <span className="text-red-500">*</span>
              </Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., Netflix Subscription"
                required
              />
            </div>

            {/* Type and Frequency */}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="type">Type</Label>
                <Select value={type} onValueChange={setType}>
                  <SelectTrigger id="type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="frequency">Frequency</Label>
                <Select value={frequency} onValueChange={setFrequency}>
                  <SelectTrigger id="frequency">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FREQUENCIES.map((f) => (
                      <SelectItem key={f.value} value={f.value}>
                        {f.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Amount */}
            <div className="grid gap-2">
              <Label htmlFor="amount">
                Amount (₹) <span className="text-red-500">*</span>
              </Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="e.g., 199"
                required
              />
            </div>

            {/* Category */}
            <div className="grid gap-2">
              <Label htmlFor="category">Category</Label>
              <Input
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g., Entertainment"
              />
            </div>

            {/* Next Due Date */}
            <div className="grid gap-2">
              <Label htmlFor="nextDueDate">Next Due Date</Label>
              <Input
                id="nextDueDate"
                type="date"
                value={nextDueDate}
                onChange={(e) => setNextDueDate(e.target.value)}
              />
            </div>

            {/* Active Status */}
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <Label htmlFor="isActive">Active</Label>
                <p className="text-xs text-muted-foreground">
                  Include this in upcoming bills timeline
                </p>
              </div>
              <Switch
                id="isActive"
                checked={isActive}
                onCheckedChange={setIsActive}
              />
            </div>

            {/* Notes */}
            <div className="grid gap-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional notes about this recurring transaction"
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!isFormValid || isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {isEditing ? "Updating..." : "Creating..."}
                </>
              ) : isEditing ? (
                "Update"
              ) : (
                "Create"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
