'use client';

import { Suspense, useState, useMemo, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, PieChart, Search, TriangleAlert, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ErrorBoundary } from '@/components/error-boundary';
import { useCategories } from '@/lib/hooks/use-finance-data';
import { CategoryBudgetList } from '@/components/categories/category-budget-list';
import { MerchantRulesTable } from '@/components/categories/merchant-rules-table';
import type { Transaction } from '@/types/transaction';
import type { UncategorizedPattern, CategorySummary } from '@/types/api';
import dynamic from 'next/dynamic';

// Dynamically import recharts to avoid SSR issues
const PieChartRecharts = dynamic(() => import('recharts').then((mod) => mod.PieChart), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const Pie = dynamic(() => import('recharts').then((mod) => mod.Pie), { ssr: false });
const Cell = dynamic(() => import('recharts').then((mod) => mod.Cell), { ssr: false });
const BarChart = dynamic(() => import('recharts').then((mod) => mod.BarChart), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const Bar = dynamic(() => import('recharts').then((mod) => mod.Bar), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false });
// @ts-expect-error - Recharts dynamic import type mismatch
const Legend = dynamic(() => import('recharts').then((mod) => mod.Legend), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), { ssr: false });

const CATEGORY_COLORS: Record<string, string> = {
  'Food & Dining': '#f97316',
  'Shopping': '#3b82f6',
  'Transportation': '#22c55e',
  'Bills & Utilities': '#ef4444',
  'Entertainment': '#a855f7',
  'Healthcare': '#ec4899',
  'Education': '#eab308',
  'Groceries': '#14b8a6',
  'Travel': '#6366f1',
  'Other': '#6b7280',
  'Transfer': '#9ca3af',
  'Uncategorized': '#9ca3af',
};

const CATEGORY_BG_COLORS: Record<string, string> = {
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

// Widget Error Fallback
function WidgetErrorFallback() {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Component Error</AlertTitle>
      <AlertDescription>
        Failed to load category component. Please try refreshing.
      </AlertDescription>
    </Alert>
  );
}

function CategoriesContent() {
  const { toast } = useToast();
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  
  // Fetch data from API
  const { data, loading, error } = useCategories();
     
  const summary = data?.summary || [];
  const monthlyBreakdown = data?.monthly_breakdown || [];
  const drillTransactions = data?.drill_transactions || [];
  const uncategorizedPatterns = data?.uncategorized_patterns || [];

  // Prepare pie chart data
  const pieData = useMemo(() => {
    return summary
      .filter((cat: CategorySummary) => cat.percentage > 0)
      .map((cat: CategorySummary) => ({
        name: cat.category,
        value: cat.amount,
        percentage: cat.percentage,
        color: CATEGORY_COLORS[cat.category] || '#6b7280',
      }));
  }, [summary]);

  // Get top categories for monthly chart
  const topCategories = useMemo(() => {
    return summary
      .slice(0, 6)
      .map((cat: CategorySummary) => cat.category);
  }, [summary]);

  // Show error toast
  useEffect(() => {
    if (error) {
      toast({
        title: 'Error loading categories',
        description: error.message,
        variant: 'destructive',
      });
    }
  }, [error, toast]);

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-[300px]" />
          <Skeleton className="h-[300px]" />
        </div>
        <Skeleton className="h-[200px]" />
      </div>
    );
  }

  // Error state
  if (error && !data) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error loading categories</AlertTitle>
        <AlertDescription>
          {error.message}. Please ensure the API server is running at http://localhost:8000
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Categories</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Spending breakdown by category and budget management
        </p>
      </div>

      {/* Budget Overview - New Modular Component */}
      <ErrorBoundary fallback={<WidgetErrorFallback />}>
        <Suspense fallback={<Skeleton className="h-[300px]" />}>
          <CategoryBudgetList />
        </Suspense>
      </ErrorBoundary>

      {/* Merchant Rules - New Modular Component */}
      <ErrorBoundary fallback={<WidgetErrorFallback />}>
        <Suspense fallback={<Skeleton className="h-[400px]" />}>
          <MerchantRulesTable />
        </Suspense>
      </ErrorBoundary>

      {/* Charts Row - Side by Side */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pie Chart - Spending Breakdown */}
        <ErrorBoundary fallback={<WidgetErrorFallback />}>
          <Suspense fallback={<Skeleton className="h-[320px]" />}>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  Spending Breakdown
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Distribution by category
                </p>
              </CardHeader>
              <CardContent className="min-h-[320px]">
                {pieData.length > 0 ? (
                  <div className="h-[280px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChartRecharts>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {pieData.map((entry: { color: string }, index: number) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--popover))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px',
                            color: 'hsl(var(--popover-foreground))',
                            fontSize: '12px',
                          }}
                          formatter={(value, name, props) => {
                            const numValue = Number(value || 0);
                             
                            const percentage = Number(props?.payload?.percentage || 0);
                            return [`₹${numValue.toLocaleString('en-IN')} (${percentage.toFixed(1)}%)`, name];
                          }}
                        />
                        <Legend 
                          verticalAlign="bottom" 
                          height={36}
                          iconType="circle"
                          formatter={(value: string) => <span className="text-xs">{value}</span>}
                        />
                      </PieChartRecharts>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-[280px] flex items-center justify-center text-muted-foreground">
                    <p>No spending data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </Suspense>
        </ErrorBoundary>

        {/* Monthly Breakdown Chart */}
        <ErrorBoundary fallback={<WidgetErrorFallback />}>
          <Suspense fallback={<Skeleton className="h-[320px]" />}>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Monthly Trend
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Top categories over time
                </p>
              </CardHeader>
              <CardContent className="min-h-[320px]">
                {monthlyBreakdown.length > 0 ? (
                  <div className="h-[280px] w-full">
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
                          formatter={(value, name) => {
                            const numValue = Number(value || 0);
                            return [`₹${numValue.toLocaleString('en-IN')}`, name];
                          }}
                        />
                        <Legend 
                          iconType="square"
                          formatter={(value: string) => <span className="text-xs">{value}</span>}
                        />
                        {topCategories.map((category) => (
                          <Bar
                            key={category}
                            dataKey={category}
                            stackId="a"
                            fill={CATEGORY_COLORS[category] || '#6b7280'}
                            radius={[0, 0, 0, 0]}
                          />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-[280px] flex items-center justify-center text-muted-foreground">
                    <p>No monthly data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </Suspense>
        </ErrorBoundary>
      </div>

      {/* Category Summary Cards */}
      {summary.length > 0 && (
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
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-sm">{cat.category}</h3>
                  <Badge variant="secondary" className="text-xs">
                    {cat.percentage.toFixed(1)}%
                  </Badge>
                </div>
                <div className="text-xl font-bold font-mono tabular-nums mb-1">
                  {cat.amount_display}
                </div>
                <p className="text-xs text-muted-foreground mb-2">
                  {cat.count} transactions
                </p>
                <Progress 
                  value={cat.percentage} 
                  className={cn("h-1.5", CATEGORY_BG_COLORS[cat.category] || 'bg-gray-500')}
                />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Category Detail with Scrollable Table */}
      <ErrorBoundary fallback={<WidgetErrorFallback />}>
        <Suspense fallback={<Skeleton className="h-[400px]" />}>
          <Card>
            <CardHeader className="pb-3">
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
                  value={selectedCategory || 'all'}
                  onValueChange={(value) => setSelectedCategory(value === 'all' ? '' : value)}
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
            <CardContent className="p-0">
              {/* Scrollable Table Container */}
              <div className="max-h-[400px] overflow-auto">
                {drillTransactions.length > 0 ? (
                  <Table>
                    <TableHeader className="sticky top-0 bg-background z-10">
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
                            txn.type === 'debit' ? 'text-rose-600' : 'text-emerald-600'
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
              </div>
            </CardContent>
          </Card>
        </Suspense>
      </ErrorBoundary>

      {/* Uncategorized Patterns */}
      {uncategorizedPatterns.length > 0 && (
        <ErrorBoundary fallback={<WidgetErrorFallback />}>
          <Suspense fallback={<Skeleton className="h-[200px]" />}>
            <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-900/10">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <TriangleAlert className="h-5 w-5 text-amber-600" />
                  <CardTitle className="text-lg font-semibold">Uncategorized Patterns</CardTitle>
                </div>
                <p className="text-sm text-muted-foreground">
                  These transactions couldn&apos;t be categorized. Add keywords to categorizer.py to fix them.
                </p>
              </CardHeader>
              <CardContent className="p-0">
                <div className="max-h-[300px] overflow-auto">
                  <Table>
                    <TableHeader className="sticky top-0 bg-amber-50/90 dark:bg-amber-900/20 z-10">
                      <TableRow>
                        <TableHead>Description</TableHead>
                        <TableHead className="w-[80px] text-center">Count</TableHead>
                        <TableHead className="w-[120px] text-right">Total Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {uncategorizedPatterns.map((pattern: UncategorizedPattern) => (
                        <TableRow key={pattern.description} className="hover:bg-amber-100/50 dark:hover:bg-amber-900/20">
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
                </div>
              </CardContent>
            </Card>
          </Suspense>
        </ErrorBoundary>
      )}
    </div>
  );
}

export default function CategoriesPage() {
  return (
    <div className="space-y-6 p-6">
      <ErrorBoundary fallback={
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Page Error</AlertTitle>
          <AlertDescription>
            Failed to load categories page. Please try refreshing.
          </AlertDescription>
        </Alert>
      }>
        <Suspense fallback={
          <div className="space-y-6">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
            <div className="grid gap-4 md:grid-cols-2">
              <Skeleton className="h-[300px]" />
              <Skeleton className="h-[300px]" />
            </div>
          </div>
        }>
          <CategoriesContent />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}
