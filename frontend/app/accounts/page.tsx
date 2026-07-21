/**
 * Accounts Page - Stage 8E-C2 Production Visual System Migration
 *
 * Relationship Explorer Surface - Main analysis surface for accounts.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 */

"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Pencil, Trash2, Building2, AlertCircle, Wallet } from "lucide-react";
import { formatINR } from "@/lib/utils/format";
import { useManagedAccounts, useCreateAccount, useUpdateAccount, useDeleteAccount, type Account } from "@/lib/hooks/use-accounts";
import { Surface } from "@/components/primitives/surface/surface";
import { Panel, PanelHeader, PanelBody } from "@/components/primitives/panel/panel";
import { Stack } from "@/components/primitives/layout/stack";
import { Grid } from "@/components/primitives/layout/grid";

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
     <Surface variant="raised" density="none" className="p-4">
       <div className="flex items-start justify-between">
         <div className="flex items-center gap-3">
           <div className="p-2 bg-gray-100 rounded-lg">
             <Building2 className="h-5 w-5 text-gray-600" />
           </div>
           <div>
             <h3 className="font-medium text-sm">{account.name}</h3>
             <p className="text-xs text-gray-500">{account.bank}</p>
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
         {account.account_number_last4 && (
           <p className="text-xs text-gray-400 mt-1">
             ••••{account.account_number_last4}
           </p>
         )}
       </div>
     </Surface>
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
    account_type: (initialData?.account_type as any) || "savings",
    // Convert from paise to rupees for form display
    balance: initialData ? (initialData.balance_paise / 100).toString() : "",
    account_number_last4: initialData?.account_number_last4 || "",
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

  // Calculate totals
  const computedTotalPaise = computedAccounts.reduce((sum, a) => sum + a.balance_paise, 0);
  const managedTotalPaise = managedData?.accounts.reduce((sum, a) => sum + a.balance_paise, 0) || 0;
  const totalBalancePaise = computedTotalPaise + managedTotalPaise;

  // Loading state
  if (computedLoading && managedLoading) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Accounts" />
          <PanelBody loading>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-40" />
              ))}
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Accounts" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* Total Balance */}
            <Surface variant="raised" density="none" className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Wallet className="h-5 w-5 text-gray-500" />
                  <span className="text-gray-600">Total Balance</span>
                </div>
                <span className="text-2xl font-bold">
                  {formatINR(totalBalancePaise)}
                </span>
              </div>
            </Surface>

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
                <Surface variant="raised" density="none" className="p-6 text-center">
                  <p className="text-gray-500">No accounts detected from statements. Import a statement to see accounts here.</p>
                </Surface>
              ) : (
                <Grid gap={4} className="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                  {computedAccounts
                    .sort((a, b) => b.balance_paise - a.balance_paise)
                    .map((account) => (
                      <Surface key={account.id} variant="raised" density="none" className="p-4">
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
                      </Surface>
                    ))}
                </Grid>
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
                <Surface variant="raised" density="none" className="p-6 text-center">
                  <p className="text-gray-500">No saved accounts. Add your first account above.</p>
                </Surface>
              ) : (
                <Grid gap={4} className="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                  {managedData?.accounts
                    .sort((a, b) => b.balance_paise - a.balance_paise)
                    .map((account) => (
                      <ManagedAccountCard
                        key={account.id}
                        account={account}
                        onEdit={handleEditManaged}
                        onDelete={handleDeleteManaged}
                      />
                    ))}
                </Grid>
              )}
            </div>
          </Stack>
        </PanelBody>
      </Panel>

      {/* Add Account Dialog - triggered by TopCommandBar */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogTrigger asChild>
          <button className="hidden" aria-hidden="true">
            Add Account
          </button>
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
    </Surface>
  );
}