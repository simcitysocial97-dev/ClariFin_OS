"use client";

/**
 * Investment Form Component
 * =========================
 *
 * Form for creating or editing an investment.
 * Handles rupees to paise conversion.
 */

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAccounts } from "@/lib/hooks/use-finance-data";
import type { Investment } from "@/lib/api/client";

// Investment type options
const INVESTMENT_TYPES = [
  { value: "mutual_fund", label: "Mutual Fund" },
  { value: "stock", label: "Stock" },
  { value: "fd", label: "Fixed Deposit" },
  { value: "ppf", label: "PPF" },
  { value: "epf", label: "EPF" },
  { value: "nps", label: "NPS" },
  { value: "gold", label: "Gold" },
  { value: "real_estate", label: "Real Estate" },
  { value: "crypto", label: "Cryptocurrency" },
  { value: "other", label: "Other" },
] as const;

export interface InvestmentFormData {
  name: string;
  type: typeof INVESTMENT_TYPES[number]["value"];
  platform: string;
  invested: string;
  current_value: string;
  units: string;
  purchase_date: string;
  maturity_date: string;
  linked_account_id: string;
  is_active: boolean;
  notes: string;
}

interface InvestmentFormProps {
  initialData?: Investment;
  onSubmit: (data: InvestmentFormData) => void;
  onCancel: () => void;
}

export function InvestmentForm({ initialData, onSubmit, onCancel }: InvestmentFormProps) {
  const { accounts } = useAccounts();
  

  const getInitialFormData = (): InvestmentFormData => {
    const invType = initialData?.type;
    return {
      name: (initialData?.name || "") as string,
      type: (invType === "mutual_fund" || invType === "stock" || invType === "fd" || invType === "ppf" || invType === "epf" || invType === "nps" || invType === "gold" || invType === "real_estate" || invType === "crypto" || invType === "other") ? invType : "mutual_fund",
      platform: (initialData?.platform || "") as string,
      invested: initialData ? String(initialData.invested_paise / 100) : "",
      current_value: initialData ? String(initialData.current_value_paise / 100) : "",
      units: initialData ? String(initialData.units) : "",
      purchase_date: (initialData?.purchase_date ? initialData.purchase_date.split("T")[0] : "") as string,
      maturity_date: (initialData?.maturity_date ? initialData.maturity_date.split("T")[0] : "") as string,
      linked_account_id: (initialData?.linked_account_id ? String(initialData.linked_account_id) : "") as string,
      is_active: initialData?.is_active ?? true,
      notes: (initialData?.notes || "") as string,
    };
  };

  const [formData, setFormData] = useState<InvestmentFormData>(getInitialFormData());

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <Label htmlFor="name">Investment Name *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., HDFC Index Fund"
            required
          />
        </div>

        <div>
          <Label htmlFor="type">Type *</Label>
          <Select
            value={formData.type}
            onValueChange={(value: typeof INVESTMENT_TYPES[number]["value"]) =>
              setFormData({ ...formData, type: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INVESTMENT_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="platform">Platform/Broker</Label>
          <Input
            id="platform"
            value={formData.platform}
            onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
            placeholder="e.g., Zerodha, Groww"
          />
        </div>

        <div>
          <Label htmlFor="invested">Amount Invested (₹) *</Label>
          <Input
            id="invested"
            type="number"
            step="0.01"
            value={formData.invested}
            onChange={(e) => setFormData({ ...formData, invested: e.target.value })}
            placeholder="0.00"
            required
          />
        </div>

        <div>
          <Label htmlFor="current_value">Current Value (₹) *</Label>
          <Input
            id="current_value"
            type="number"
            step="0.01"
            value={formData.current_value}
            onChange={(e) => setFormData({ ...formData, current_value: e.target.value })}
            placeholder="0.00"
            required
          />
        </div>

        <div>
          <Label htmlFor="units">Units/Quantity</Label>
          <Input
            id="units"
            type="number"
            step="0.001"
            value={formData.units}
            onChange={(e) => setFormData({ ...formData, units: e.target.value })}
            placeholder="0.000"
          />
        </div>

        <div>
          <Label htmlFor="purchase_date">Purchase Date</Label>
          <Input
            id="purchase_date"
            type="date"
            value={formData.purchase_date}
            onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
          />
        </div>

        <div>
          <Label htmlFor="maturity_date">Maturity Date</Label>
          <Input
            id="maturity_date"
            type="date"
            value={formData.maturity_date}
            onChange={(e) => setFormData({ ...formData, maturity_date: e.target.value })}
          />
        </div>

        <div>
          <Label htmlFor="status">Status</Label>
          <Select
            value={formData.is_active ? "active" : "inactive"}
            onValueChange={(value) => setFormData({ ...formData, is_active: value === "active" })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="linked_account">Linked Account</Label>
          <Select
            value={formData.linked_account_id}
            onValueChange={(value) => setFormData({ ...formData, linked_account_id: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select account" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">None</SelectItem>
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
            placeholder="Any additional notes..."
            rows={3}
            className="w-full px-3 py-2 border rounded-md text-sm min-h-[80px] resize-y focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      <div className="flex gap-2 pt-4">
        <Button type="submit" className="flex-1">
          {initialData ? "Update Investment" : "Add Investment"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
