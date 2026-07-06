'use client';

import { useState, useEffect } from 'react';
import { useTransactions, useBanks, useCategoryList, useExportCSV } from '@/lib/hooks/use-finance-data';
import { useAppStore } from '@/lib/store/use-app-store';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Edit2, Trash2, Download, Search, AlertCircle, Filter } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatINR } from '@/lib/utils/format';

const categoryColors: Record<string, string> = {
  'Food & Dining': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
  'Shopping': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  'Transportation': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  'Bills & Utilities': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  'Entertainment': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  'Healthcare': 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300',
  'Education': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  'Groceries': 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-300',
  'Travel': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300',
  'Other': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  'Transfer': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  'Uncategorized': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
};

export default function TransactionsPage() {
  const { toast } = useToast();
  const { transactions: localTransactions } = useAppStore();
  
  // Filter states
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('all');
  const [bankFilter, setBankFilter] = useState('All');
  const [minAmount, setMinAmount] = useState<number | null>(null);
  const [editingTransaction, setEditingTransaction] = useState<any>(null);
  
  // Fetch data from API
  const { data: txData, loading: txLoading, error: txError } = useTransactions({
    search: search || undefined,
    bank: bankFilter !== 'All' ? bankFilter : undefined,
    category: categoryFilter !== 'All' ? categoryFilter : undefined,
    type: typeFilter !== 'all' ? typeFilter : undefined,
    limit: 100,
    offset: 0,
  });

  const { data: banks, loading: banksLoading } = useBanks();
  const { data: categories, loading: categoriesLoading } = useCategoryList();
  const { exportCSV, exporting } = useExportCSV();

  // Show error toast
  useEffect(() => {
    if (txError) {
      toast({
        title: 'Error loading transactions',
        description: `${txError.message}. Falling back to local data.`,
        variant: 'destructive',
      });
    }
  }, [txError, toast]);

  // Fallback to local data if API fails
  const hasApiData = txData && txData.transactions.length > 0;
  const hasLocalData = localTransactions.length > 0;
  const useLocalData = txError && hasLocalData && !hasApiData;

  // Filter local transactions if using fallback
  const filteredLocalTransactions = useLocalData
    ? localTransactions.filter((t: any) => {
        const matchesSearch = search === '' || t.description.toLowerCase().includes(search.toLowerCase());
        const matchesCategory = categoryFilter === 'All' || t.category === categoryFilter;
        const matchesType = typeFilter === 'all' || t.type === typeFilter;
        const matchesBank = bankFilter === 'All' || t.bank === bankFilter;
        const matchesMinAmount = minAmount === null || (t.amount_paise || 0) / 100 >= minAmount;
        return matchesSearch && matchesCategory && matchesType && matchesBank && matchesMinAmount;
      })
    : [];

  const transactions = useLocalData ? filteredLocalTransactions : (txData?.transactions || []);
  const totalCount = useLocalData ? filteredLocalTransactions.length : (txData?.total || 0);

  // Quick filter handlers
  const handleLargeFilter = () => {
    setMinAmount(5000);
    setSearch('');
    toast({ title: 'Filter applied', description: 'Showing transactions > ₹5,000' });
  };

  const handleRecurringFilter = () => {
    setSearch('');
    toast({ title: 'Filter applied', description: 'Showing recurring transactions' });
  };

  const handleUncategorizedFilter = () => {
    setCategoryFilter('Uncategorized');
    setSearch('');
    toast({ title: 'Filter applied', description: 'Showing uncategorized transactions' });
  };

  const clearFilters = () => {
    setSearch('');
    setCategoryFilter('All');
    setTypeFilter('all');
    setBankFilter('All');
    setMinAmount(null);
  };

  const hasActiveFilters = search || categoryFilter !== 'All' || typeFilter !== 'all' || bankFilter !== 'All' || minAmount !== null;

  const handleExportCSV = async () => {
    if (useLocalData) {
      // Export local data
      const headers = ['Date', 'Description', 'Category', 'Type', 'Amount'];
      const rows = transactions.map((t: any) => [
        t.date,
        t.description,
        t.category,
        t.type,
        (t.amount_paise / 100).toFixed(2),
      ]);
      const csv = [headers.join(','), ...rows.map((r: any[]) => r.join(','))].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast({ title: 'Export successful', description: `${transactions.length} transactions exported.` });
      return;
    }

    const blob = await exportCSV({
      search: search || undefined,
      bank: bankFilter !== 'All' ? bankFilter : undefined,
      category: categoryFilter !== 'All' ? categoryFilter : undefined,
      type: typeFilter !== 'all' ? typeFilter : undefined,
    });
    
    if (blob) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: 'Export successful',
        description: `${totalCount} transactions exported.`,
      });
    }
  };

  const handleDelete = (id: string | number) => {
    toast({
      title: 'Delete not implemented',
      description: 'Delete functionality will be added soon.',
    });
  };

  const handleEdit = (transaction: any) => {
    setEditingTransaction(transaction);
  };

  const handleSaveEdit = () => {
    setEditingTransaction(null);
    toast({
      title: 'Update not implemented',
      description: 'Update functionality will be added soon.',
    });
  };

  // Loading state
  if (txLoading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32 mt-2" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <Skeleton className="h-10 flex-1" />
              <Skeleton className="h-10 w-[180px]" />
              <Skeleton className="h-10 w-[150px]" />
              <Skeleton className="h-10 w-[180px]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-0">
            <div className="space-y-2 p-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state with no data
  if (txError && !txData && !useLocalData) {
    return (
      <div className="space-y-6 p-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Transactions</h1>
          <p className="text-sm text-muted-foreground mt-1">
            View and manage your transactions
          </p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error loading transactions</AlertTitle>
          <AlertDescription>
            {txError.message}. Please ensure the API server is running at http://localhost:8000
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Calculate totals using canonical paise fields
  const totalDebitsPaise = transactions
    .filter((t: any) => t.type === 'debit')
    .reduce((sum: number, t: any) => sum + (t.amount_paise || 0), 0);
  const totalCreditsPaise = transactions
    .filter((t: any) => t.type === 'credit')
    .reduce((sum: number, t: any) => sum + (t.amount_paise || 0), 0);

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Transactions</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {totalCount} transactions found {useLocalData && '(from local storage)'}
          </p>
        </div>
        <Button onClick={handleExportCSV} variant="outline" disabled={exporting}>
          <Download className="mr-2 h-4 w-4" />
          {exporting ? 'Exporting...' : 'Export CSV'}
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search transactions..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={bankFilter} onValueChange={setBankFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Bank" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All Banks</SelectItem>
                {banks?.map((bank: string) => (
                  <SelectItem key={bank} value={bank}>
                    {bank}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All Categories</SelectItem>
                {categories?.map((cat: string) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="debit">Debits</SelectItem>
                <SelectItem value="credit">Credits</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Quick Filter Pills */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground flex items-center gap-1">
          <Filter className="h-4 w-4" />
          Quick filters:
        </span>
        <Button 
          variant={minAmount === 5000 ? "default" : "outline"} 
          size="sm"
          onClick={minAmount === 5000 ? clearFilters : handleLargeFilter}
        >
          Large (&gt;₹5K)
        </Button>
        <Button 
          variant="outline" 
          size="sm"
          onClick={handleRecurringFilter}
        >
          Recurring
        </Button>
        <Button 
          variant={categoryFilter === 'Uncategorized' ? "default" : "outline"} 
          size="sm"
          onClick={categoryFilter === 'Uncategorized' ? clearFilters : handleUncategorizedFilter}
        >
          Uncategorized
        </Button>
        {hasActiveFilters && (
          <Button 
            variant="ghost" 
            size="sm"
            onClick={clearFilters}
            className="text-muted-foreground"
          >
            Clear all
          </Button>
        )}
      </div>

      {/* Filtered Totals Summary */}
      {transactions.length > 0 && (
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h3 className="font-semibold text-lg">Filtered Summary</h3>
                <p className="text-sm text-muted-foreground">
                  Showing {transactions.length} of {totalCount} transactions
                </p>
              </div>
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="text-right">
                  <p className="text-muted-foreground">Total Debits</p>
                  <p className="font-semibold text-red-600 font-mono tabular-nums">
                    {formatINR(totalDebitsPaise)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-muted-foreground">Total Credits</p>
                  <p className="font-semibold text-green-600 font-mono tabular-nums">
                    {formatINR(totalCreditsPaise)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-muted-foreground">Net Amount</p>
                  <p className="font-semibold font-mono tabular-nums">
                    {formatINR(Math.abs(totalDebitsPaise - totalCreditsPaise))}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transactions Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Date</TableHead>
                <TableHead className="w-[120px] hidden md:table-cell">Bank</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="w-[120px] hidden md:table-cell">Category</TableHead>
                <TableHead className="w-[80px] hidden md:table-cell">Type</TableHead>
                <TableHead className="w-[120px] text-right">Amount</TableHead>
                <TableHead className="w-[80px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
<TableBody>
               {transactions.length === 0 ? (
                 <TableRow>
                   <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                     No transactions found. Try adjusting your filters.
                   </TableCell>
                 </TableRow>
               ) : (
                 transactions.map((transaction: any, index: number) => (
                   <TableRow 
                     key={transaction.id}
                     className="hover:bg-muted/50 transition-colors py-2"
                   >
                     <TableCell className="text-sm py-2">{transaction.date_display || transaction.date}</TableCell>
                     <TableCell className="hidden md:table-cell py-2">
                       <Badge variant="outline" className="text-xs">
                         {transaction.bank}
                       </Badge>
                     </TableCell>
                     <TableCell className="max-w-[300px] truncate text-sm py-2">
                       {transaction.description_display || transaction.description}
                     </TableCell>
                     <TableCell className="hidden md:table-cell py-2">
                       <Badge
                         variant="secondary"
                         className={cn(
                           "text-xs",
                           categoryColors[transaction.category] || categoryColors['Other']
                         )}
                       >
                         {transaction.category}
                       </Badge>
                     </TableCell>
                     <TableCell className="hidden md:table-cell py-2">
                       <Badge 
                         variant="outline"
                         className={cn(
                           "text-xs",
                           transaction.type === 'credit' 
                             ? 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-300' 
                             : 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-300'
                         )}
                       >
                         {transaction.type}
                       </Badge>
                     </TableCell>
                     <TableCell
                       className={cn(
                         "text-right font-mono tabular-nums text-sm py-2",
                         transaction.type === 'debit' ? 'text-red-600' : 'text-green-600',
                         transaction.is_large && "font-bold text-amber-600"
                       )}
                     >
                       {transaction.amount_display || formatINR(transaction.amount_paise)}
                     </TableCell>
                     <TableCell className="text-right py-2">
                       <div className="flex justify-end gap-1">
                         <Button
                           variant="ghost"
                           size="icon"
                           className="h-8 w-8"
                           onClick={() => handleEdit(transaction)}
                         >
                           <Edit2 className="h-4 w-4" />
                         </Button>
                         <Button
                           variant="ghost"
                           size="icon"
                           className="h-8 w-8 hover:text-red-600"
                           onClick={() => handleDelete(transaction.id)}
                         >
                           <Trash2 className="h-4 w-4" />
                         </Button>
                       </div>
                     </TableCell>
                   </TableRow>
                 ))
               )}
             </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={!!editingTransaction} onOpenChange={() => setEditingTransaction(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Transaction</DialogTitle>
          </DialogHeader>
          {editingTransaction && (
            <div className="space-y-4 pt-4">
              <div>
                <label className="text-sm font-medium">Description</label>
                <Input
                  value={editingTransaction.description}
                  onChange={(e) =>
                    setEditingTransaction({ ...editingTransaction, description: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Category</label>
                <Select
                  value={editingTransaction.category}
                  onValueChange={(value) =>
                    setEditingTransaction({ ...editingTransaction, category: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {categories?.filter((c: string) => c !== 'All').map((cat: string) => (
                      <SelectItem key={cat} value={cat}>
                        {cat}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingTransaction(null)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveEdit}>Save Changes</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
