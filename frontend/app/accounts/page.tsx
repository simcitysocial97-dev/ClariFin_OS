'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PageShell } from '@/components/layout/page-shell';
import { KpiCard } from '@/components/ui/kpi-card';
import { useAccounts, useCreateAccount, useUpdateAccount, useDeleteAccount } from '@/lib/hooks/use-finance-data';
import { formatINR, formatDate, formatAccountType, getAccountTypeColor, paiseToRupees } from '@/lib/format';
import { Plus, Pencil, Trash2, Building2, Wallet, Landmark, Wallet2, TrendingUp } from 'lucide-react';
import type { Account } from '@/lib/api/client';

const ACCOUNT_TYPES = [
  { value: 'savings', label: 'Savings Account', icon: Wallet },
  { value: 'current', label: 'Current Account', icon: Wallet2 },
  { value: 'fd', label: 'Fixed Deposit', icon: Landmark },
  { value: 'wallet', label: 'Wallet', icon: Wallet },
] as const;

const BANK_SUGGESTIONS = ['HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Mahindra Bank', 'Punjab National Bank', 'Bank of Baroda', 'Other'];

const PRESET_COLORS = [
  '#6366F1', '#8B5CF6', '#EC4899', '#F43F5E', '#10B981', '#06B6D4', '#3B82F6', '#F59E0B',
];

// ============================================================
// Types
// ============================================================

interface AccountFormData {
  name: string;
  bank_name: string;
  account_type: typeof ACCOUNT_TYPES[number]['value'];
  account_number_masked: string;
  balance_rupees: string;
  color: string;
  is_active: boolean;
}

// ============================================================
// Account Form
// ============================================================

function AccountForm({ initialData, onSubmit, onCancel }: { initialData?: Account; onSubmit: (data: AccountFormData) => void; onCancel: () => void }) {
  const [formData, setFormData] = useState<AccountFormData>({
    name: initialData?.name || '',
    bank_name: initialData?.bank_name || '',
    account_type: (initialData?.account_type as typeof ACCOUNT_TYPES[number]['value']) || 'savings',
    account_number_masked: initialData?.account_number_masked || 'XXXX',
    balance_rupees: initialData ? String(paiseToRupees(initialData.balance_paise || 0)) : '',
    color: (initialData?.color || PRESET_COLORS[0]) as string,
    is_active: initialData?.is_active ?? true,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="bank_name">Bank Name</Label>
          <Select value={formData.bank_name} onValueChange={(v) => setFormData({ ...formData, bank_name: v })}>
            <SelectTrigger>
              <SelectValue placeholder="Select bank" />
            </SelectTrigger>
            <SelectContent>
              {BANK_SUGGESTIONS.map((bank) => (
                <SelectItem key={bank} value={bank}>{bank}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="account_type">Account Type</Label>
          <Select value={formData.account_type} onValueChange={(v) => setFormData({ ...formData, account_type: v as any })}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ACCOUNT_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">Account Name</Label>
          <Input id="name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="e.g., Primary Savings" required />
        </div>
        <div>
          <Label htmlFor="account_number_masked">Account Number (Last 4)</Label>
          <Input id="account_number_masked" value={formData.account_number_masked} onChange={(e) => setFormData({ ...formData, account_number_masked: e.target.value })} maxLength={4} />
        </div>
      </div>

      <div>
        <Label>Color</Label>
        <div className="flex gap-2 flex-wrap">
          {PRESET_COLORS.map((color) => (
            <button key={color} type="button" className={`w-8 h-8 rounded-full border-2 transition-all ${formData.color === color ? 'border-foreground scale-110' : 'border-transparent'}`} style={{ backgroundColor: color }} onClick={() => setFormData({ ...formData, color })} />
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input id="is_active" type="checkbox" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} className="rounded" />
        <Label htmlFor="is_active">Active</Label>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
        <Button type="submit">{initialData ? 'Update Account' : 'Add Account'}</Button>
      </div>
    </form>
  );
}

// ============================================================
// Main
// ============================================================

export default function AccountsPage() {
  const { accounts } = useAccounts();
  const { createAccount } = useCreateAccount();
  const { updateAccount } = useUpdateAccount();
  const { deleteAccount } = useDeleteAccount();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | undefined>(undefined);

  const filteredAccounts = (accounts ?? []).filter((a) => a.account_type !== 'credit_card');

  const totalBalancePaise = filteredAccounts.reduce((sum, a) => sum + (a.balance_paise || 0), 0);

  const handleCreate = async (formData: AccountFormData) => {
    createAccount({
      name: formData.name,
      bank_name: formData.bank_name,
      account_type: formData.account_type,
      account_number_masked: formData.account_number_masked,
      balance: parseFloat(formData.balance_rupees) || 0,
      currency: 'INR',
      color: formData.color,
      icon: 'building',
      is_active: formData.is_active,
    } as any);
    setDialogOpen(false);
  };

  const handleUpdate = async (formData: AccountFormData) => {
    if (!editingAccount) return;
    updateAccount({
      id: editingAccount.id,
      account: {
        name: formData.name,
        bank_name: formData.bank_name,
        account_type: formData.account_type,
        account_number_masked: formData.account_number_masked,
        balance: parseFloat(formData.balance_rupees) || 0,
        color: formData.color,
        is_active: formData.is_active,
      } as any,
    });
    setEditingAccount(undefined);
    setDialogOpen(false);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this account?')) return;
    deleteAccount(id);
    setEditingAccount(undefined);
  };

  return (
    <PageShell
      title="Accounts"
      subtitle={`${filteredAccounts.length} account${filteredAccounts.length === 1 ? '' : 's'}`}
      actions={
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-2" />Add Account</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>{editingAccount ? 'Edit Account' : 'Add Account'}</DialogTitle></DialogHeader>
            <AccountForm initialData={editingAccount} onSubmit={editingAccount ? handleUpdate : handleCreate} onCancel={() => { setEditingAccount(undefined); setDialogOpen(false); }} />
          </DialogContent>
        </Dialog>
      }
    >
      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <KpiCard title="Total Balance" value={formatINR(totalBalancePaise)} subtext="Across all active accounts" icon={<Wallet className="h-5 w-5" />} />
        <KpiCard title="Last Updated" value={filteredAccounts.length ? formatDate(filteredAccounts[0]?.updated_at) : '—'} subtext={`${filteredAccounts.length} total`} icon={<TrendingUp className="h-5 w-5" />} />
      </div>

      {/* Accounts Grid */}
      {filteredAccounts.length === 0 ? (
        <Card className="p-8 text-center">
          <Building2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-medium mb-2">No Accounts Yet</h3>
          <p className="text-muted-foreground mb-4">Add your first bank account to track balances.</p>
          <Button onClick={() => setDialogOpen(true)}><Plus className="h-4 w-4 mr-2" />Add Account</Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAccounts.map((account) => (
            <div key={account.id} className="rounded-xl border bg-card p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg" style={{ backgroundColor: `${account.color}20` }}>
                    <Building2 className="h-5 w-5" style={{ color: account.color }} />
                  </div>
                  <div>
                    <h3 className="font-medium">{account.name}</h3>
                    <p className="text-sm text-muted-foreground">{account.bank_name}</p>
                    <Badge variant="secondary" className={`mt-1 text-xs ${getAccountTypeColor(account.account_type)}`}>{formatAccountType(account.account_type)}</Badge>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" onClick={() => { setEditingAccount(account); setDialogOpen(true); }}><Pencil className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon" onClick={() => handleDelete(account.id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Balance</span>
                  <span className="text-lg font-bold">{formatINR(account.balance_paise)}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">Updated: {formatDate(account.updated_at)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </PageShell>
  );
}