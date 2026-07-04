"use client";

/**
 * Income Source Dialog
 * ====================
 * Dialog for creating and editing income sources.
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
import type { IncomeSource, IncomeSourceCreate, IncomeSourceUpdate } from "@/types/income";

// ============================================================
// Constants
// ============================================================

const INCOME_TYPES = [
  { value: "salary", label: "Salary" },
  { value: "freelance", label: "Freelance" },
  { value: "business", label: "Business" },
  { value: "rental", label: "Rental" },
  { value: "dividend", label: "Dividend" },
  { value: "interest", label: "Interest" },
  { value: "other", label: "Other" },
] as const;

const FREQUENCIES = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "annual", label: "Annual" },
  { value: "irregular", label: "Irregular" },
] as const;

// ============================================================
// Types
// ============================================================

interface IncomeSourceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  source?: IncomeSource | null;
  onSubmit: (data: IncomeSourceCreate | IncomeSourceUpdate) => Promise<void>;
  isSubmitting?: boolean;
}

// ============================================================
// Component
// ============================================================

export function IncomeSourceDialog({
  open,
  onOpenChange,
  source,
  onSubmit,
  isSubmitting = false,
}: IncomeSourceDialogProps) {
  const isEditing = !!source;

  // Form state
  const [name, setName] = useState("");
  const [type, setType] = useState<string>("salary");
  const [amount, setAmount] = useState<string>("");
  const [frequency, setFrequency] = useState<string>("monthly");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [isActive, setIsActive] = useState<boolean>(true);
  const [notes, setNotes] = useState<string>("");

  // Reset form when dialog opens/closes or source changes
  useEffect(() => {
    if (open) {
      if (source) {
        // Edit mode - populate form
        setName(source.name);
        setType(source.type);
        setAmount((source.amount_paise / 100).toString());
        setFrequency(source.frequency);
        setStartDate(source.start_date || "");
        setEndDate(source.end_date || "");
        setIsActive(source.is_active);
        setNotes(source.notes || "");
      } else {
        // Create mode - reset form
        setName("");
        setType("salary");
        setAmount("");
        setFrequency("monthly");
        setStartDate("");
        setEndDate("");
        setIsActive(true);
        setNotes("");
      }
    }
  }, [open, source]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const amountRupees = parseFloat(amount);
    if (isNaN(amountRupees) || amountRupees < 0) {
      return;
    }

    const baseData = {
      name,
      type: type as IncomeSource["type"],
      amount_paise: rupeesToPaise(amountRupees),
      frequency: frequency as IncomeSource["frequency"],
      start_date: startDate || null,
      end_date: endDate || null,
      is_active: isActive,
      notes: notes || null,
    };

    if (isEditing && source) {
      // Only include changed fields for update
      const updateData: IncomeSourceUpdate = {};
      if (name !== source.name) updateData.name = name;
      if (type !== source.type) updateData.type = type as IncomeSource["type"];
      if (baseData.amount_paise !== source.amount_paise) updateData.amount_paise = baseData.amount_paise;
      if (frequency !== source.frequency) updateData.frequency = frequency as IncomeSource["frequency"];
      if (baseData.start_date !== source.start_date) updateData.start_date = baseData.start_date;
      if (baseData.end_date !== source.end_date) updateData.end_date = baseData.end_date;
      if (isActive !== source.is_active) updateData.is_active = isActive;
      if (baseData.notes !== source.notes) updateData.notes = baseData.notes;
      
      await onSubmit(updateData);
    } else {
      await onSubmit(baseData as IncomeSourceCreate);
    }
  };

  const isFormValid = name.trim() !== "" && amount !== "" && !isNaN(parseFloat(amount));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <Edit2 className="h-5 w-5" />
                  Edit Income Source
                </>
              ) : (
                <>
                  <Plus className="h-5 w-5" />
                  Add Income Source
                </>
              )}
            </DialogTitle>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Name */}
            <div className="grid gap-2">
              <Label htmlFor="name">
                Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Monthly Salary"
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
                    {INCOME_TYPES.map((t) => (
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
                placeholder="e.g., 50000"
                required
              />
            </div>

            {/* Dates */}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="startDate">Start Date</Label>
                <Input
                  id="startDate"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="endDate">End Date</Label>
                <Input
                  id="endDate"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>

            {/* Active Status */}
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <Label htmlFor="isActive">Active</Label>
                <p className="text-xs text-muted-foreground">
                  Include this income in calculations
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
                placeholder="Optional notes about this income source"
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
