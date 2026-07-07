"use client";

/**
 * Accounts Page - Personal Finance MVP v1.0.0
 * ==========================================
 * 
 * Simple CRUD for managing savings accounts.
 * Backend owns all balances - no localStorage.
 * 
 * Phase 1: Updated to use balance_paise (canonical) and formatINR formatter.
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

// ============================================================
// Types
// ============================================================

interface Account {
  id: string;
  name: string;
  bank_name: string;
  account_type: "Savings" | "Current" | "FD" | "RD";
  balance_paise: number;  // Canonical field (in paise)
  balance_rupees?: number;  // Deprecated - for backward compatibility
  last_updated: string;
}

interface AccountFormData {
  name: string;
  bank_name: string;
  account_type: "Savings" | "Current" | "FD" | "RD";
  balance: string;
}

// ============================================================
// Components
// ============================================================

function AccountCard({ account, onEdit, onDelete }: { 
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
               <p className="text-xs text-gray-500">{account.bank_name}</p>
               <span className="inline-block mt-1 text-xs bg-gray-100 px-2 py-0.5 rounded">
                 {account.account_type}
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
             <span className="text-lg font-semibold">{formatINR(account.balance_paise)}</span>
           </div>
           <p className="text-xs text-gray-400 mt-1">
             Updated: {new Date(account.last_updated).toLocaleDateString()}
           </p>
         </div>
       </CardContent>
     </Card>
   );
}

function AccountForm({ 
  initialData, 
  onSubmit, 
  onCancel 
}: { 
  initialData?: Account; 
  onSubmit: (data: AccountFormData) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<AccountFormData>({
    name: initialData?.name || "",
    bank_name: initialData?.bank_name || "",
    account_type: initialData?.account_type || "Savings",
    // Convert from paise to rupees for form display
    balance: initialData ? (initialData.balance_paise / 100).toString() : "",
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
        <Label htmlFor="bank_name">Bank Name</Label>
        <Input
          id="bank_name"
          value={formData.bank_name}
          onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
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
            <SelectItem value="Savings">Savings</SelectItem>
            <SelectItem value="Current">Current</SelectItem>
            <SelectItem value="FD">Fixed Deposit (FD)</SelectItem>
            <SelectItem value="RD">Recurring Deposit (RD)</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label htmlFor="balance">Current Balance</Label>
        <Input
          id="balance"
          type="number"
          value={formData.balance}
          onChange={(e) => setFormData({ ...formData, balance: e.target.value })}
          placeholder="0"
          required
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
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);

  // Fetch accounts
  useEffect(() => {
    async function fetchAccounts() {
      try {
        const response = await fetch("http://localhost:8000/api/accounts");
        if (!response.ok) throw new Error("Failed to fetch accounts");
        const data = await response.json();
        setAccounts(data.accounts || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    }
    fetchAccounts();
  }, []);

  // Create account
  const handleCreate = async (formData: AccountFormData) => {
    try {
      const response = await fetch("http://localhost:8000/api/accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          balance: parseFloat(formData.balance),
        }),
      });
      if (!response.ok) throw new Error("Failed to create account");
      const newAccount = await response.json();
      setAccounts([...accounts, newAccount]);
      setDialogOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create account");
    }
  };

  // Update account
  const handleUpdate = async (formData: AccountFormData) => {
    if (!editingAccount) return;
    try {
      const response = await fetch(`http://localhost:8000/api/accounts/${editingAccount.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          balance: parseFloat(formData.balance),
        }),
      });
      if (!response.ok) throw new Error("Failed to update account");
      const updatedAccount = await response.json();
      setAccounts(accounts.map(a => a.id === updatedAccount.id ? updatedAccount : a));
      setEditingAccount(null);
      setDialogOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update account");
    }
  };

  // Delete account
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this account?")) return;
    try {
      const response = await fetch(`http://localhost:8000/api/accounts/${id}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to delete account");
      setAccounts(accounts.filter(a => a.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete account");
    }
  };

  // Edit handler
  const handleEdit = (account: Account) => {
    setEditingAccount(account);
    setDialogOpen(true);
  };

  // Add new handler
  const handleAddNew = () => {
    setEditingAccount(null);
    setDialogOpen(true);
  };

  // Calculate total - use balance_paise (in paise)
  const totalBalancePaise = accounts.reduce((sum, a) => sum + a.balance_paise, 0);

  // Loading state
  if (loading) {
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

  // Error state
  if (error) {
    return (
      <div className="container mx-auto py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
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
            <Button onClick={handleAddNew}>
              <Plus className="mr-2 h-4 w-4" />
              Add Account
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingAccount ? "Edit Account" : "Add New Account"}</DialogTitle>
            </DialogHeader>
            <AccountForm
              initialData={editingAccount || undefined}
              onSubmit={editingAccount ? handleUpdate : handleCreate}
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

      {/* Accounts Grid */}
      {accounts.length === 0 ? (
        <Card className="p-8 text-center">
          <Building2 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium mb-2">No Accounts Yet</h3>
          <p className="text-gray-500 mb-4">Add your first savings account to track your balances.</p>
          <Button onClick={handleAddNew}>
            <Plus className="mr-2 h-4 w-4" />
            Add Account
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts
            .sort((a, b) => b.balance_paise - a.balance_paise)
            .map((account) => (
              <AccountCard
                key={account.id}
                account={account}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
        </div>
      )}
    </div>
  );
}