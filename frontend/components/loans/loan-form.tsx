"use client";

/**
 * Loan Form Component
 * ===================
 *
 * Form for creating or editing a loan.
 * Handles rupees to paise conversion.
 */

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAccounts } from "@/lib/hooks/use-finance-data";
import type { Loan } from "@/lib/api/client";

// Loan type options
export const LOAN_TYPES = [
  { value: "home", label: "Home Loan" },
  { value: "car", label: "Car Loan" },
  { value: "personal", label: "Personal Loan" },
  { value: "education", label: "Education Loan" },
  { value: "credit_card", label: "Credit Card" },
  { value: "gold", label: "Gold Loan" },
  { value: "other", label: "Other" },
] as const;

// Status options
export const LOAN_STATUS = [
  { value: "active", label: "Active" },
  { value: "closed", label: "Closed" },
  { value: "defaulted", label: "Defaulted" },
] as const;

export interface LoanFormData {
  name: string;
  lender: string;
  loan_type: typeof LOAN_TYPES[number]["value"];
  principal: string;
  outstanding: string;
  interest_rate: string;
  emi: string;
  tenure_months: string;
  start_date: string;
  end_date: string;
  linked_account_id: string;
  status: typeof LOAN_STATUS[number]["value"];
  notes: string;
}

interface LoanFormProps {
  initialData?: Loan;
  onSubmit: (data: LoanFormData) => void;
  onCancel: () => void;
}

export function LoanForm({ initialData, onSubmit, onCancel }: LoanFormProps) {
  const { accounts } = useAccounts();
  

  const getInitialFormData = (): LoanFormData => {
    const loanType = initialData?.loan_type;
    const status = initialData?.status;
    
    return {
      name: (initialData?.name || "") as string,
      lender: (initialData?.lender || "") as string,
      loan_type: ((loanType === "home" || loanType === "car" || loanType === "personal" || 
                  loanType === "education" || loanType === "credit_card" || loanType === "gold" || 
                  loanType === "other") ? loanType : "personal") as LoanFormData["loan_type"],
      principal: initialData ? String(initialData.principal_paise / 100) : "",
      outstanding: initialData ? String(initialData.outstanding_paise / 100) : "",
      interest_rate: initialData ? String(initialData.interest_rate) : "",
      emi: initialData ? String((initialData.emi_paise || 0) / 100) : "",
      tenure_months: (initialData?.tenure_months ? String(initialData.tenure_months) : "") as string,
      start_date: (initialData?.start_date ? initialData.start_date.split("T")[0] : "") as string,
      end_date: (initialData?.end_date ? initialData.end_date.split("T")[0] : "") as string,
      linked_account_id: (initialData?.linked_account_id ? String(initialData.linked_account_id) : "") as string,
      status: ((status === "active" || status === "closed" || status === "defaulted") ? status : "active") as LoanFormData["status"],
      notes: (initialData?.notes || "") as string,
    };
  };

  const [formData, setFormData] = useState<LoanFormData>(getInitialFormData());

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <Label htmlFor="name">Loan Name *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Home Loan HDFC"
            required
          />
        </div>

        <div>
          <Label htmlFor="lender">Lender/Bank</Label>
          <Input
            id="lender"
            value={formData.lender}
            onChange={(e) => setFormData({ ...formData, lender: e.target.value })}
            placeholder="e.g., HDFC Bank"
          />
        </div>

        <div>
          <Label htmlFor="loan_type">Loan Type *</Label>
          <Select
            value={formData.loan_type}
            onValueChange={(value: typeof LOAN_TYPES[number]["value"]) =>
              setFormData({ ...formData, loan_type: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LOAN_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="principal">Principal Amount (₹) *</Label>
          <Input
            id="principal"
            type="number"
            step="0.01"
            value={formData.principal}
            onChange={(e) => setFormData({ ...formData, principal: e.target.value })}
            placeholder="0.00"
            required
          />
        </div>

        <div>
          <Label htmlFor="outstanding">Outstanding Amount (₹) *</Label>
          <Input
            id="outstanding"
            type="number"
            step="0.01"
            value={formData.outstanding}
            onChange={(e) => setFormData({ ...formData, outstanding: e.target.value })}
            placeholder="0.00"
            required
          />
        </div>

        <div>
          <Label htmlFor="interest_rate">Interest Rate (% p.a.) *</Label>
          <Input
            id="interest_rate"
            type="number"
            step="0.01"
            value={formData.interest_rate}
            onChange={(e) => setFormData({ ...formData, interest_rate: e.target.value })}
            placeholder="8.5"
            required
          />
        </div>

        <div>
          <Label htmlFor="emi">Monthly EMI (₹)</Label>
          <Input
            id="emi"
            type="number"
            step="0.01"
            value={formData.emi}
            onChange={(e) => setFormData({ ...formData, emi: e.target.value })}
            placeholder="0.00"
          />
        </div>

        <div>
          <Label htmlFor="tenure_months">Tenure (Months)</Label>
          <Input
            id="tenure_months"
            type="number"
            value={formData.tenure_months}
            onChange={(e) => setFormData({ ...formData, tenure_months: e.target.value })}
            placeholder="120"
          />
        </div>

        <div>
          <Label htmlFor="start_date">Start Date *</Label>
          <Input
            id="start_date"
            type="date"
            value={formData.start_date}
            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            required
          />
        </div>

        <div>
          <Label htmlFor="end_date">End Date</Label>
          <Input
            id="end_date"
            type="date"
            value={formData.end_date}
            onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
          />
        </div>

        <div>
          <Label htmlFor="status">Status</Label>
          <Select
            value={formData.status}
            onValueChange={(value: typeof LOAN_STATUS[number]["value"]) =>
              setFormData({ ...formData, status: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LOAN_STATUS.map((status) => (
                <SelectItem key={status.value} value={status.value}>
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="linked_account">Linked Account</Label>
          <Select
            value={formData.linked_account_id || "none"}
            onValueChange={(value) => setFormData({ ...formData, linked_account_id: value === "none" ? "" : value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select account" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              {accounts.map((account) => (
                <SelectItem key={account.id} value={String(account.id)}>
                  {account.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="col-span-2">
          <Label htmlFor="notes">Notes</Label>
          <textarea
            id="notes"
            value={formData.notes}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, notes: e.target.value })}
            placeholder="Any additional notes about this loan..."
            rows={3}
            className="w-full px-3 py-2 border rounded-md text-sm min-h-[80px] resize-y focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      <div className="flex gap-2 pt-4">
        <Button type="submit" className="flex-1">
          {initialData ? "Update Loan" : "Add Loan"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
