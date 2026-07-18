'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DataStateWrapper } from '@/components/ui/data-state-wrapper';

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
};

interface TransactionItem {
  id: string | number;
  date: string;
  description: string;
  category: string;
  type: 'debit' | 'credit' | string;
  amount_paise: number;
  amount?: number;
  amount_display?: string;
  description_display?: string;
  is_large?: boolean;
}

interface RecentTransactionsProps {
  transactions: TransactionItem[];
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
}

export function RecentTransactions({ 
  transactions, 
  isLoading = false, 
  isError = false, 
  onRetry 
}: RecentTransactionsProps) {
  const isEmpty = !isLoading && !isError && transactions.length === 0;

  return (
    <DataStateWrapper
      isLoading={isLoading}
      isError={isError}
      isEmpty={isEmpty}
      emptyMessage="No transactions yet. Upload a statement to get started."
      onRetry={onRetry}
    >
      <div className="space-y-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Date</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="w-[120px]">Category</TableHead>
              <TableHead className="w-[100px] text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((transaction) => (
              <TableRow 
                key={transaction.id}
                className="hover:bg-muted/50 transition-colors"
              >
                <TableCell className="text-sm">{transaction.date}</TableCell>
                <TableCell className="max-w-[200px] truncate text-sm">
                  {transaction.description_display || transaction.description}
                </TableCell>
                <TableCell>
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
                <TableCell className={cn(
                  "text-right font-mono tabular-nums text-sm",
                  transaction.type === 'debit' ? 'text-red-600' : 'text-green-600',
                  transaction.is_large && "font-bold text-amber-600"
                )}>
                  {transaction.amount_display || `${transaction.type === 'debit' ? '-' : '+'}₹${(transaction.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        <div className="flex justify-end">
          <Link href="/transactions">
            <Button variant="ghost" size="sm">
              View all transactions
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </DataStateWrapper>
  );
}