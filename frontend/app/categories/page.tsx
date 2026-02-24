'use client';

import { useState } from 'react';
import { useCategories } from '@/lib/hooks/use-finance-data';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, PieChart, Search, TriangleAlert } from 'lucide-react';
import { cn } from '@/lib/utils';
import dynamic from 'next/dynamic';
import type { Transaction } from '@/types/transaction';
import type { UncategorizedPattern, CategorySummary } from '@/types/api';

// Dynamically import recharts to avoid SSR issues
const BarChart = dynamic(() => import('recharts').then((mod) => mod.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then((mod) => mod.Bar), { ssr: false });
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), { ssr: false });

const categoryColors: Record<string, string> = {
  'Food & Dining': 'bg-orange-500',
  'Shopping': 'bg-blue-500',
  'Transportation': 'bg-green-500',
  'Bills & Utilities': 'bg-red-500',
  'Entertainment': 'bg-purple-500',
  'Healthcare': 'bg-pink-500',
  'Education': 'bg-yellow-500',
  'Groceries': 'bg-teal-500',
  'Travel': 'bg-indigo-500',
  'Other': 'bg-gray-500',
  'Transfer': 'bg-gray-400',
  'Uncategorized': 'bg-gray-400',
};

export default function CategoriesPage() {
  const { toast } = useToast();
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  
  // Fetch data from API
  const { data: categoriesData, loading, error } = useCategories({
    drill_category: selectedCategory || undefined,
  });

  const summary = categoriesData?.summary || [];
  const monthlyBreakdown = categoriesData?.monthly_breakdown || [];
  const drillTransactions = categoriesData?.drill_transactions || [];
  const uncategorizedPatterns = categoriesData?.uncategorized_patterns || [];

  // Show error toast
  useState(() => {
    if (error) {
      toast({
        title: 'Error loading categories',
        description: error.message,
        variant: 'destructive',
      });
    }
  });

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-6 w-32 mb-2" />
                <Skeleton className="h-8 w-24 mb-4" />
                <Skeleton className="h-2 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error && !categoriesData) {
    return (
      <div className="space-y-6 p-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Categories</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Spending breakdown by category
          </p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error loading categories</AlertTitle>
          <AlertDescription>
            {error.message}. Please ensure the API server is running at http://localhost:8000
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Categories</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Spending breakdown by category
        </p>
      </div>

      {/* Category Summary Cards */}
      {summary.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {summary.map((cat: CategorySummary) => (
            <Card 
              key={cat.category}
              className={cn(
                "cursor-pointer transition-all hover:shadow-md",
                selectedCategory === cat.category && "ring-2 ring-primary"
              )}
              onClick={() => setSelectedCategory(selectedCategory === cat.category ? '' : cat.category)}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-sm">{cat.category}</h3>
                  <Badge variant="secondary" className="text-xs">
                    {cat.percentage_display}
                  </Badge>
                </div>
                <div className="text-2xl font-bold font-mono tabular-nums mb-1">
                  {cat.amount_display}
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  {cat.count_display}
                </p>
                <Progress 
                  value={cat.percentage} 
                  className={cn("h-2", categoryColors[cat.category] || 'bg-gray-500')}
                />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <PieChart className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">No category data available</p>
          </CardContent>
        </Card>
      )}

      {/* Monthly Category Breakdown Chart */}
      {monthlyBreakdown.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Monthly Category Breakdown</CardTitle>
            <p className="text-sm text-muted-foreground">Spending by category over time</p>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyBreakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground) / 0.2)" />
                  <XAxis 
                    dataKey="month" 
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis 
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--popover))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      color: 'hsl(var(--popover-foreground))',
                      fontSize: '12px',
                    }}
                    formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Amount']}
                  />
                  <Bar dataKey="amount" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Drill-Down */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-lg font-semibold">Category Detail</CardTitle>
              <p className="text-sm text-muted-foreground">
                {selectedCategory 
                  ? `Transactions in ${selectedCategory}` 
                  : 'Select a category to see transactions'}
              </p>
            </div>
            <Select
              value={selectedCategory}
              onValueChange={setSelectedCategory}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {summary.map((cat: CategorySummary) => (
                  <SelectItem key={cat.category} value={cat.category}>
                    {cat.category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {drillTransactions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="w-[120px] text-right">Amount</TableHead>
                  <TableHead className="w-[120px]">Bank</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {drillTransactions.map((txn: Transaction) => (
                  <TableRow key={txn.id} className="hover:bg-muted/50">
                    <TableCell className="text-sm">{txn.date_display || txn.date}</TableCell>
                    <TableCell className="text-sm">{txn.description_display || txn.description}</TableCell>
                    <TableCell className={cn(
                      "text-right font-mono tabular-nums text-sm",
                      txn.type === 'debit' ? 'text-red-600' : 'text-green-600'
                    )}>
                      {txn.amount_display || `₹${txn.amount.toLocaleString('en-IN')}`}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {txn.bank}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm">
                {selectedCategory 
                  ? 'No transactions found in this category' 
                  : 'Select a category above to see transactions'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Uncategorized Patterns */}
      {uncategorizedPatterns.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-900/10">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TriangleAlert className="h-5 w-5 text-amber-600" />
              <CardTitle className="text-lg font-semibold">Uncategorized Patterns</CardTitle>
            </div>
            <p className="text-sm text-muted-foreground">
              These transactions couldn't be categorized. Add keywords to categorizer.py to fix them.
            </p>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Description</TableHead>
                  <TableHead className="w-[80px] text-center">Count</TableHead>
                  <TableHead className="w-[120px] text-right">Total Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {uncategorizedPatterns.map((pattern: UncategorizedPattern) => (
                  <TableRow key={pattern.description} className="hover:bg-muted/50">
                    <TableCell className="text-sm font-mono">{pattern.description}</TableCell>
                    <TableCell className="text-center">
                      <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800">
                        {pattern.count}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono tabular-nums text-sm">
                      {pattern.total_display || `₹${pattern.total.toLocaleString('en-IN')}`}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}