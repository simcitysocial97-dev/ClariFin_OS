"use client";

/**
 * Accounts Page - Personal Finance MVP v1.0.0
 * ==========================================
 * 
 * Two sections:
 * 1. Computed Accounts - derived from transaction statements
 * 2. Managed Accounts - persistent DB-backed accounts
 * 
 * Phase 4: Added managed accounts section with DB persistence.
 */

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Pencil, Trash2, Building2, AlertCircle, Wallet } from "lucide-react";
import { formatINR } from "@/lib/utils/format";
import { useManagedAccounts, useCreateAccount, useUpdateAccount, useDeleteAccount, type Account } from "@/lib/hooks/use-accounts";

// ============================================================
// Types for Computed Accounts (from /api/accounts)
// ============================================================

interface ComputedAccount {
  id: string;
  name: string;
  bank: string;
  balance_paise: number;
  transaction_count: number;
}

// ============================================================
// Types for Managed Accounts Form
// ============================================================

interface ManagedAccountFormData {
  name: string;
  bank: string;
  account_type: "savings" | "current" | "salary" | "fd" | "nre" | "nro";
  balance: string;
  account_number_last4: string;
  notes: string;
}

// ============================================================
// Components
// ============================================================

function ManagedAccountCard({ account, onEdit, onDelete }: { 
  account: Account; 
  onEdit: (account: Account) => void;
  onDelete: (id: string) => void;
}) {
  return (
     <Card>
       <CardContent className="p-4">
         <div className="flex items-start justify-between">
           <div className="flex items-center gap-3">
             <div className="p-2 bg-gray-100 rounded-lg">
               <Building2 className="h-5 w-5 text-gray-600" />
             </div>
             <div>
               <h3 className="font-medium text-sm">{account.name}</h3>
               <p className="text-xs text-gray-500">{account.bank}</p>
<span className="inline-block mt-1 text-xs bg-gray-100 px-2 py-0.5 rounded">
                  {account.accountType}
                </span>
             </div>
           </div>
           <div className="flex items-center gap-1">
             <Button variant="ghost" size="sm" onClick={() => onEdit(account)}>
               <Pencil className="h-4 w-4" />
             </Button>
             <Button variant="ghost" size="sm" onClick={() => onDelete(account.id)}>
               <Trash2 className="h-4 w-4 text-red-500" />
             </Button>
           </div>
         </div>
         <div className="mt-3 pt-2 border-t">
           <div className="flex items-center justify-between">
             <span className="text-xs text-gray-500">Balance</span>
             <span className="text-lg font-semibold">{formatINR(account.balancePaise)}</span>
           </div>
           {account.accountNumberLast4 && (
             <p className="text-xs text-gray-400 mt-1">
               ••••{account.accountNumberLast4}
             </p>
           )}
         </div>
       </CardContent>
     </Card>
   );
}

function ManagedAccountForm({ 
  initialData, 
  onSubmit, 
  onCancel 
}: { 
  initialData?: Account; 
  onSubmit: (data: ManagedAccountFormData) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<ManagedAccountFormData>({
    name: initialData?.name || "",
    bank: initialData?.bank || "",
    account_type: (initialData?.accountType as any) || "savings",
    // Convert from paise to rupees for form display
    balance: initialData ? (initialData.balancePaise / 100).toString() : "",
    account_number_last4: initialData?.accountNumberLast4 || "",
    notes: initialData?.notes || "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="name">Account Name</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="e.g., Primary Savings"
          required
        />
      </div>
      <div>
        <Label htmlFor="bank">Bank Name</Label>
        <Input
          id="bank"
          value={formData.bank}
          onChange={(e) => setFormData({ ...formData, bank: e.target.value })}
          placeholder="e.g., HDFC Bank"
          required
        />
      </div>
      <div>
        <Label htmlFor="account_type">Account Type</Label>
        <Select
          value={formData.account_type}
          onValueChange={(value: any) => setFormData({ ...formData, account_type: value })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="savings">Savings</SelectItem>
            <SelectItem value="current">Current</SelectItem>
            <SelectItem value="salary">Salary</SelectItem>
            <SelectItem value="fd">Fixed Deposit (FD)</SelectItem>
            <SelectItem value="nre">NRE</SelectItem>
            <SelectItem value="nro">NRO</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label htmlFor="balance">Current Balance (₹)</Label>
        <Input
          id="balance"
          type="number"
          step="0.01"
          value={formData.balance}
          onChange={(e) => setFormData({ ...formData, balance: e.target.value })}
          placeholder="0.00"
          required
        />
      </div>
      <div>
        <Label htmlFor="account_number_last4">Last 4 Digits (optional)</Label>
        <Input
          id="account_number_last4"
          value={formData.account_number_last4}
          onChange={(e) => setFormData({ ...formData, account_number_last4: e.target.value })}
          placeholder="1234"
          maxLength={4}
        />
      </div>
      <div>
        <Label htmlFor="notes">Notes (optional)</Label>
        <Input
          id="notes"
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          placeholder="Any notes"
        />
      </div>
      <div className="flex gap-2 pt-2">
        <Button type="submit" className="flex-1">
          {initialData ? "Update Account" : "Add Account"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function AccountsPage() {
  // Computed accounts state (from /api/accounts)
  const [computedAccounts, setComputedAccounts] = useState<ComputedAccount[]>([]);
  const [computedLoading, setComputedLoading] = useState(true);
  const [computedError, setComputedError] = useState<string | null>(null);

  // Managed accounts state (from /api/accounts/manage)
  const { data: managedData, isLoading: managedLoading, error: managedError } = useManagedAccounts();
  const createAccountMutation = useCreateAccount();
  const updateAccountMutation = useUpdateAccount();
  const deleteAccountMutation = useDeleteAccount();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);

  // Fetch computed accounts
  useEffect(() => {
    async function fetchComputedAccounts() {
      try {
        const response = await fetch("http://localhost:8000/api/accounts");
        if (!response.ok) throw new Error("Failed to fetch accounts");
        const data = await response.json();
        setComputedAccounts(data.accounts || []);
      } catch (err) {
        setComputedError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setComputedLoading(false);
      }
    }
    fetchComputedAccounts();
  }, []);

  // Managed account handlers
  const handleCreateManaged = async (formData: ManagedAccountFormData) => {
    try {
      const balancePaise = Math.round(parseFloat(formData.balance) * 100);
      await createAccountMutation.mutateAsync({
        name: formData.name,
        bank: formData.bank,
        account_type: formData.account_type,
        balance_paise: balancePaise,
        account_number_last4: formData.account_number_last4 || undefined,
        notes: formData.notes || undefined,
      });
      setDialogOpen(false);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleUpdateManaged = async (formData: ManagedAccountFormData) => {
    if (!editingAccount) return;
    try {
      const balancePaise = Math.round(parseFloat(formData.balance) * 100);
      await updateAccountMutation.mutateAsync({
        id: editingAccount.id,
        name: formData.name,
        bank: formData.bank,
        account_type: formData.account_type,
        balance_paise: balancePaise,
        account_number_last4: formData.account_number_last4 || undefined,
        notes: formData.notes || undefined,
      });
      setEditingAccount(null);
      setDialogOpen(false);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleDeleteManaged = async (id: string) => {
    if (!confirm("Are you sure you want to delete this account?")) return;
    try {
      await deleteAccountMutation.mutateAsync(id);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleEditManaged = (account: Account) => {
    setEditingAccount(account);
    setDialogOpen(true);
  };

  const handleAddNewManaged = () => {
    setEditingAccount(null);
    setDialogOpen(true);
  };

  // Calculate totals
  const computedTotalPaise = computedAccounts.reduce((sum, a) => sum + a.balance_paise, 0);
  const managedTotalPaise = managedData?.accounts.reduce((sum, a) => sum + a.balancePaise, 0) || 0;
  const totalBalancePaise = computedTotalPaise + managedTotalPaise;

  // Loading state
  if (computedLoading && managedLoading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Accounts</h1>
          <p className="text-gray-500 text-sm">Manage your savings accounts</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleAddNewManaged}>
              <Plus className="mr-2 h-4 w-4" />
              Add Account
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingAccount ? "Edit Account" : "Add New Account"}</DialogTitle>
            </DialogHeader>
            <ManagedAccountForm
              initialData={editingAccount || undefined}
              onSubmit={editingAccount ? handleUpdateManaged : handleCreateManaged}
              onCancel={() => {
                setEditingAccount(null);
                setDialogOpen(false);
              }}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Total Balance */}
      <Card className="bg-gray-50">
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wallet className="h-5 w-5 text-gray-500" />
              <span className="text-gray-600">Total Balance</span>
            </div>
            <span className="text-2xl font-bold">
              {formatINR(totalBalancePaise)}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Section 1: Computed Accounts (from statements) */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Detected Accounts</h2>
        <p className="text-sm text-gray-500 mb-4">Accounts derived from imported statements</p>
        {computedError && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{computedError}</AlertDescription>
          </Alert>
        )}
        {computedAccounts.length === 0 ? (
          <Card className="p-6 text-center">
            <p className="text-gray-500">No accounts detected from statements. Import a statement to see accounts here.</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {computedAccounts
              .sort((a, b) => b.balance_paise - a.balance_paise)
              .map((account) => (
                <Card key={account.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gray-100 rounded-lg">
                        <Building2 className="h-5 w-5 text-gray-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-sm">{account.name}</h3>
                        <p className="text-xs text-gray-500">{account.bank}</p>
                      </div>
                    </div>
                    <div className="mt-3 pt-2 border-t">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">Balance</span>
                        <span className="text-lg font-semibold">{formatINR(account.balance_paise)}</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {account.transaction_count} transactions
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
          </div>
        )}
      </div>

      {/* Section 2: Managed Accounts (persistent) */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Saved Accounts</h2>
        <p className="text-sm text-gray-500 mb-4">Manually added accounts with persistent balances</p>
        {managedError && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{managedError.message}</AlertDescription>
          </Alert>
        )}
        {managedData?.accounts.length === 0 ? (
          <Card className="p-6 text-center">
            <p className="text-gray-500">No saved accounts. Add your first account above.</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {managedData?.accounts
              .sort((a, b) => b.balancePaise - a.balancePaise)
              .map((account) => (
                <ManagedAccountCard
                  key={account.id}
                  account={account}
                  onEdit={handleEditManaged}
                  onDelete={handleDeleteManaged}
                />
              ))}
          </div>
        )}
      </div>
    </div>
  );
}