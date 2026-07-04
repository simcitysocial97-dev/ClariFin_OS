'use client';

import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PageShell } from '@/components/layout/page-shell';
import {
  useTransactions,
  useAccounts,
  useV2Imports,
  useUpdateCategory,
} from '@/lib/hooks/use-finance-data';
import { useCategories } from '@/lib/hooks/use-finance-data';
import { formatINR, formatDate } from '@/lib/format';
import {
  Download,
  Upload,
  Search,
  X,
  ChevronDown,
  CheckCircle2,
  Clock,
  Edit3,
  MoreHorizontal,
} from 'lucide-react';
import type { Transaction } from '@/types/transaction';

// API returns extended transaction objects with nature and account_name
interface ApiTransaction extends Transaction {
  nature?: string;
  account_name?: string;
  total_pages?: number;
  raw_text?: string;
}

// Types
type NatureType = 'all' | 'real_income' | 'real_expense' | 'recycling_in' | 'recycling_out' | 'interest_charge' | 'inter_account' | 'unknown';

const NATURE_OPTIONS: { value: NatureType; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'real_income', label: 'Income' },
  { value: 'real_expense', label: 'Expenses' },
  { value: 'recycling_in', label: 'Recycling In' },
  { value: 'recycling_out', label: 'Recycling Out' },
  { value: 'interest_charge', label: 'Interest Charge' },
  { value: 'inter_account', label: 'Inter-Account' },
  { value: 'unknown', label: 'Unknown' },
];

const NATURE_COLORS: Record<string, string> = {
  real_income: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  real_expense: 'bg-muted text-muted-foreground',
  recycling_in: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  recycling_out: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  interest_charge: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  inter_account: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  unknown: 'bg-gray-100 text-gray-700 dark:bg-gray-900/40 dark:text-gray-300',
};

const QUICK_FILTERS = ['All', 'Income', 'Expenses', 'Recycling', 'Unknown', 'This Month', 'Last Month'];

// ============================================================
// Main
// ============================================================

export default function TransactionsPage() {
  const [search, setSearch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [natureFilter, setNatureFilter] = useState<NatureType>('all');
  const [minAmount, setMinAmount] = useState('');
  const [maxAmount, setMaxAmount] = useState('');
  const [page, setPage] = useState(1);
  const [selectedTx, setSelectedTx] = useState<ApiTransaction | null>(null);
  const [importDrawerOpen, setImportDrawerOpen] = useState(false);
  const [editCategoryId, setEditCategoryId] = useState<string | number | null>(null);
  const [editCategoryValue, setEditCategoryValue] = useState('');
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);

  const { transactions, loading, error, refetch } = useTransactions();
  const { accounts } = useAccounts();
  const { categories } = useCategories();
  const { data: importHistory } = useV2Imports();
  const updateCategoryMutation = useUpdateCategory();

  // Enrich transactions with account_name (client-side join)
  const enrichedTransactions = useMemo(() => {
    return transactions.map((tx) => ({
      ...tx,
      account_name: accounts?.find((acc: any) => acc.id === tx.account_id)?.name || '—',
    }));
  }, [transactions, accounts]);

  // Summary derived from filtered set
  const summary = useMemo(() => {
    let credits = 0;
    let debits = 0;
    enrichedTransactions.forEach((tx) => {
      if ((tx.amount_paise ?? 0) >= 0) credits += tx.amount_paise ?? 0;
      else debits += tx.amount_paise ?? 0;
    });
    return { credits, debits, net: credits + debits, count: enrichedTransactions.length };
  }, [enrichedTransactions]);

  // Total count for pagination
  const totalCount = enrichedTransactions.length;

  const handleExportCSV = async () => {
    const csv = serializeToCSV(transactions);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // CSV helper
  function serializeToCSV(transactions: ApiTransaction[]): string {
    if (!transactions.length) return '';
    const headers = ['Date', 'Description', 'Amount', 'Nature', 'Category', 'Account'];
    const rows = transactions.map((tx) => [
      tx.date,
      tx.description,
      tx.amount_paise ?? 0,
      tx.nature ?? '',
      tx.category ?? '',
      tx.account_name ?? '',
    ]);
    const csv = [headers, ...rows].map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','));
    return csv.join('\n');
  }

  const clearFilters = () => {
    setSearch('');
    setStartDate('');
    setEndDate('');
    setSelectedAccounts([]);
    setNatureFilter('all');
    setMinAmount('');
    setMaxAmount('');
    setPage(1);
  };

  const hasFilters = search || startDate || endDate || selectedAccounts.length > 0 || natureFilter !== 'all' || minAmount || maxAmount;

  const openCategoryEditor = (tx: Transaction) => {
    setEditCategoryId(tx.id);
    setEditCategoryValue(tx.category || '');
    setCategoryDialogOpen(true);
  };

  const saveCategory = async () => {
    if (!editCategoryId) return;
    await updateCategoryMutation.update({ id: Number(editCategoryId), category: editCategoryValue, subcategory: undefined });
    setCategoryDialogOpen(false);
    setEditCategoryId(null);
    refetch();
  };

  return (
    <PageShell
      title="Transactions"
      subtitle={`${totalCount} transactions found`}
      actions={
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExportCSV}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Sheet open={importDrawerOpen} onOpenChange={setImportDrawerOpen}>
            <SheetTrigger asChild>
              <Button>
                <Upload className="h-4 w-4 mr-2" />
                Import Statement
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-full sm:max-w-lg">
              <SheetHeader>
                <SheetTitle>Import Statement</SheetTitle>
              </SheetHeader>
              <div className="mt-4 space-y-4">
                <Card className="border-muted-foreground/20 border-dashed">
                  <div className="p-6 text-center text-sm text-muted-foreground">
                    Drag-and-drop PDF dropzone placeholder
                  </div>
                </Card>
                <div>
                  <h4 className="text-sm font-semibold mb-2">Recent Imports</h4>
                  <div className="space-y-2">
                    {(Array.isArray(importHistory) ? importHistory : []).slice(0, 5).map((imp: any) => (
                      <div key={imp.id} className="flex items-center justify-between text-sm border rounded-lg px-3 py-2">
                        <div className="flex items-center gap-2">
                          {imp.status === 'completed' ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          ) : (
                            <Clock className="h-4 w-4 text-amber-600" />
                          )}
                          <span className="truncate">{imp.file_name}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">{formatDate(imp.created_at)}</span>
                      </div>
                    ))}
                    {(!Array.isArray(importHistory) || importHistory.length === 0) && (
                      <p className="text-xs text-muted-foreground">No recent imports.</p>
                    )}
                  </div>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      }
    >
      {/* Filter bar */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
          <div className="md:col-span-3 relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search description"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="md:col-span-2">
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div className="md:col-span-2">
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <div className="md:col-span-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  <span className="truncate">
                    {selectedAccounts.length === 0
                      ? 'All Accounts'
                      : `${selectedAccounts.length} selected`}
                  </span>
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="start">
                <DropdownMenuLabel>Accounts</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {(accounts ?? []).map((acc: any) => (
                  <DropdownMenuCheckboxItem
                    key={acc.id}
                    checked={selectedAccounts.includes(acc.id.toString())}
                    onCheckedChange={(checked) => {
                      setSelectedAccounts((prev) =>
                        checked
                          ? [...prev, acc.id.toString()]
                          : prev.filter((id) => id !== acc.id.toString())
                      );
                    }}
                  >
                    {acc.name}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          <div className="md:col-span-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  <span className="truncate">
                    {natureFilter === 'all' ? 'All Natures' : natureFilter.replace('_', ' ')}
                  </span>
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="start">
                <DropdownMenuLabel>Nature</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {NATURE_OPTIONS.map((opt) => (
                  <DropdownMenuCheckboxItem
                    key={opt.value}
                    checked={natureFilter === opt.value}
                    onCheckedChange={() => setNatureFilter(opt.value)}
                  >
                    {opt.label}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          <div className="md:col-span-1 flex">
            {hasFilters && (
              <Button variant="ghost" size="icon" onClick={clearFilters} className="shrink-0">
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Amount range */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 mt-3">
          <div className="md:col-span-5">
            <Input
              placeholder="Min amount (₹)"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              type="number"
            />
          </div>
          <div className="md:col-span-5">
            <Input
              placeholder="Max amount (₹)"
              value={maxAmount}
              onChange={(e) => setMaxAmount(e.target.value)}
              type="number"
            />
          </div>
        </div>
      </Card>

      {/* Quick filters */}
      <div className="flex flex-wrap items-center gap-2">
        {QUICK_FILTERS.map((q) => (
          <Button
            key={q}
            variant="outline"
            size="sm"
            onClick={() => {
              if (q === 'All') clearFilters();
              else if (q === 'Income') setNatureFilter('real_income');
              else if (q === 'Expenses') setNatureFilter('real_expense');
              else if (q === 'Recycling') setNatureFilter('recycling_out');
              else if (q === 'Unknown') setNatureFilter('unknown');
              else if (q === 'This Month') {
                const now = new Date();
                setStartDate(new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0] ?? '');
                setEndDate(new Date().toISOString().split('T')[0] ?? '');
              } else if (q === 'Last Month') {
                const now = new Date();
                const first = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                const last = new Date(now.getFullYear(), now.getMonth(), 0);
                setStartDate(first.toISOString().split('T')[0] ?? '');
                setEndDate(last.toISOString().split('T')[0] ?? '');
              }
            }}
          >
            {q}
          </Button>
        ))}
      </div>

      {/* Summary row */}
      <div className="flex flex-wrap items-center gap-4 text-sm">
        <span className="text-emerald-700 dark:text-emerald-400">Credits: {formatINR(summary.credits)}</span>
        <span className="text-red-700 dark:text-red-400">Debits: {formatINR(summary.debits)}</span>
        <span className="font-medium">Net: {formatINR(summary.net)}</span>
        <span className="text-muted-foreground">Count: {summary.count}</span>
      </div>

      {/* Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="text-left px-4 py-3 w-28">Date</th>
                <th className="text-left px-4 py-3">Description</th>
                <th className="text-left px-4 py-3 w-36">Account</th>
                <th className="text-left px-4 py-3 w-32">Category</th>
                <th className="text-left px-4 py-3 w-40">Nature</th>
                <th className="text-right px-4 py-3 w-28">Amount</th>
                <th className="text-right px-4 py-3 w-20">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    Loading transactions…
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-red-600">
                    {error.message}
                  </td>
                </tr>
              ) : enrichedTransactions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    No transactions match your filters.
                  </td>
                </tr>
              ) : (
                enrichedTransactions.map((tx) => (
                  <tr
                    key={tx.id}
                    className="border-b last:border-0 hover:bg-muted/40 transition-colors"
                    onClick={() => setSelectedTx(tx)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">{formatDate(tx.date)}</td>
                    <td className="px-4 py-3">
                      <span className="truncate block max-w-[320px]" title={tx.description}>
                        {tx.description}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">{tx.account_name ?? '—'}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          openCategoryEditor(tx);
                        }}
                      >
                        {tx.category || 'Uncategorized'}
                        <Edit3 className="h-3 w-3 ml-1" />
                      </Button>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {tx.nature ? (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${NATURE_COLORS[tx.nature] || NATURE_COLORS.unknown}`}>
                          {tx.nature.replace('_', ' ')}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className={`px-4 py-3 text-right whitespace-nowrap font-medium ${(tx.amount_paise ?? 0) >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                      {formatINR(tx.amount_paise)}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTx(tx);
                        }}
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalCount > 50 && (
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <span className="text-xs text-muted-foreground">
              Page {page}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page * 50 >= totalCount}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </Card>

      {/* Transaction detail + category editor */}
      <Dialog open={!!selectedTx} onOpenChange={(open) => !open && setSelectedTx(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Transaction Detail</DialogTitle>
          </DialogHeader>
          {selectedTx && (
            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted-foreground">Description</p>
                <p className="text-sm font-medium">{selectedTx.description}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Date</p>
                  <p className="font-medium">{formatDate(selectedTx.date)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Amount</p>
                  <p className="font-medium">{formatINR(selectedTx.amount_paise)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Account</p>
                  <p className="font-medium">{selectedTx.account_name ?? '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Category</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openCategoryEditor(selectedTx)}
                  >
                    {selectedTx.category || 'Set category'}
                  </Button>
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Nature</p>
                <span className={`inline-block text-[10px] px-1.5 py-0.5 rounded ${NATURE_COLORS[selectedTx.nature || 'unknown'] || NATURE_COLORS.unknown}`}>
                  {selectedTx.nature?.replace('_', ' ') || 'unknown'}
                </span>
              </div>
              {selectedTx.raw_text && (
                <div>
                  <p className="text-xs text-muted-foreground">Raw</p>
                  <p className="text-xs bg-muted rounded p-2 max-h-24 overflow-auto">{selectedTx.raw_text}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Category editor */}
      <Dialog open={categoryDialogOpen} onOpenChange={setCategoryDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Category</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Select value={editCategoryValue} onValueChange={setEditCategoryValue}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {(categories ?? []).map((cat) => (
                  <SelectItem key={cat.category} value={cat.category}>
                    {cat.category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setCategoryDialogOpen(false)}>Cancel</Button>
              <Button onClick={saveCategory} disabled={updateCategoryMutation.updating}>
                {updateCategoryMutation.updating ? 'Saving…' : 'Save'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </PageShell>
  );
}
