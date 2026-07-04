'use client';

import { useAnalytics } from '@/lib/hooks/use-finance-data';
import { useToast } from '@/hooks/use-toast';
import type { MerchantData, RecurringCharge, LargestTransaction } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { TrendingUp, BarChart3, Zap, Store, AlertCircle, Repeat, ArrowUpRight } from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
} from '@/components/ui/recharts';

interface StatCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ElementType;
}

function StatCard({ title, value, subtitle, icon: Icon }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold font-mono tabular-nums">{value}</div>
        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const { data: analytics, loading, error } = useAnalytics();
  const { toast } = useToast();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Show error toast
  useEffect(() => {
    if (error) {
      toast({
        title: 'Error loading analytics',
        description: error.message,
        variant: 'destructive',
      });
    }
  }, [error, toast]);

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
                <Skeleton className="h-3 w-24 mt-2" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="h-[400px]">
            <CardHeader>
              <Skeleton className="h-6 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[300px] w-full" />
            </CardContent>
          </Card>
          <Card className="h-[400px]">
            <CardHeader>
              <Skeleton className="h-6 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[300px] w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !analytics) {
    return (
      <div className="space-y-6 p-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Deep insights into your spending patterns
          </p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error loading analytics</AlertTitle>
          <AlertDescription>
            {error.message}. Please ensure the API server is running at http://localhost:8000
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Stat cards from API
  const statCards = [
    {
      title: 'Highest Month',
      value: analytics?.highest_month_amount || '₹0',
      subtitle: analytics?.highest_month || 'No data',
      icon: TrendingUp,
    },
    {
      title: 'Avg Monthly',
      value: analytics?.avg_monthly_display || '₹0',
      subtitle: 'per month',
      icon: BarChart3,
    },
    {
      title: 'Biggest Transaction',
      value: analytics?.biggest_txn_amount || '₹0',
      subtitle: analytics?.biggest_txn_desc || 'No data',
      icon: Zap,
    },
    {
      title: 'Unique Merchants',
      value: analytics?.unique_merchants_display || '0',
      subtitle: 'distinct payees',
      icon: Store,
    },
  ];

  // Chart data
  const spendingTrend = analytics?.spending_trend || [];
  const dayOfWeekData = analytics?.day_of_week_data || [];
  const topMerchants = analytics?.top_merchants || [];
  const recurringCharges = analytics?.recurring_charges || [];
  const largestTransactions = analytics?.largest_transactions || [];

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics & Insights</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Deep insights into your spending patterns
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <StatCard key={stat.title} {...stat} />
        ))}
      </div>

      {/* Spending Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Spending Trend</CardTitle>
          <p className="text-sm text-muted-foreground">Monthly spend over time with average reference</p>
        </CardHeader>
        <CardContent className="min-h-[320px]">
          {mounted && spendingTrend.length > 0 ? (
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={spendingTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground) / 0.2)" vertical={false} />
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
                    tickFormatter={(value: number) => `₹${(value / 1000).toFixed(0)}K`}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--popover))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      color: 'hsl(var(--popover-foreground))',
                      fontSize: '12px',
                    }}
                    formatter={(value: number) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Amount']}
                  />
                  <Area
                    type="monotone"
                    dataKey="amount"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    fill="hsl(var(--primary))"
                    fillOpacity={0.1}
                  />
                  <Line
                    type="monotone"
                    dataKey="average"
                    stroke="hsl(var(--muted-foreground))"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[280px] flex items-center justify-center text-muted-foreground">
              No spending trend data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Two Column Layout: Day of Week + Top Merchants */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Day of Week Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Day of Week Pattern</CardTitle>
            <p className="text-sm text-muted-foreground">Total spend by weekday</p>
          </CardHeader>
          <CardContent className="min-h-[260px]">
            {mounted && dayOfWeekData.length > 0 ? (
              <div className="h-[220px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dayOfWeekData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground) / 0.2)" horizontal={false} />
                    <XAxis 
                      dataKey="day" 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(value: number) => `₹${(value / 1000).toFixed(0)}K`}
                    />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'hsl(var(--popover))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                        color: 'hsl(var(--popover-foreground))',
                        fontSize: '12px',
                      }}
                      formatter={(value: number) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Amount']}
                    />
                    <Bar dataKey="amount" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-muted-foreground">
              No day of week data available
            </div>
          )}
        </CardContent>
      </Card>

        {/* Top Merchants Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Top Merchants</CardTitle>
            <p className="text-sm text-muted-foreground">By total spend</p>
          </CardHeader>
          <CardContent className="min-h-[260px]">
            {topMerchants.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Merchant</TableHead>
                    <TableHead className="w-[60px] text-center">Count</TableHead>
                    <TableHead className="w-[100px] text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topMerchants.map((merchant: MerchantData, index: number) => (
                    <TableRow key={`merchant-${index}-${merchant.name}`} className="hover:bg-muted/50">
                      <TableCell className="text-sm">{merchant.name}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant="secondary" className="text-xs">
                          {merchant.count_display || merchant.count}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums text-sm">
                        {merchant.amount_display || `₹${merchant.amount.toLocaleString('en-IN')}`}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No merchant data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Side by Side: Recurring Charges & Largest Transactions */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recurring Charges Table */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Repeat className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg font-semibold">Recurring Charges</CardTitle>
            </div>
            <p className="text-xs text-muted-foreground">
              Transactions appearing 2+ times with consistent amounts
            </p>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[300px] overflow-auto">
              {recurringCharges.length > 0 ? (
                <Table>
                  <TableHeader className="sticky top-0 bg-background z-10">
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead className="w-[60px] text-center">Freq</TableHead>
                      <TableHead className="w-[90px] text-right">Avg</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recurringCharges.slice(0, 10).map((charge: RecurringCharge, index: number) => (
                      <TableRow key={`recurring-${index}-${charge.description}`} className="hover:bg-muted/50">
                        <TableCell className="text-sm truncate max-w-[150px]">{charge.description}</TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary" className="text-xs bg-indigo-100 text-indigo-800">
                            {charge.frequency_display || `${charge.frequency}x`}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono tabular-nums text-sm">
                          {charge.avg_display || `₹${charge.avg_amount.toLocaleString('en-IN')}`}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  No recurring charges detected
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Largest Transactions Table */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <ArrowUpRight className="h-5 w-5 text-red-500" />
              <CardTitle className="text-lg font-semibold">Largest Transactions</CardTitle>
            </div>
            <p className="text-xs text-muted-foreground">Top expenses by amount</p>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[300px] overflow-auto">
              {largestTransactions.length > 0 ? (
                <Table>
                  <TableHeader className="sticky top-0 bg-background z-10">
                    <TableRow>
                      <TableHead className="w-[40px]">#</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="w-[100px] text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {largestTransactions.slice(0, 10).map((txn: LargestTransaction) => (
                      <TableRow key={txn.rank} className="hover:bg-muted/50">
                        <TableCell className="text-sm text-muted-foreground">{txn.rank}</TableCell>
                        <TableCell className="text-sm truncate max-w-[180px]">{txn.description_display || txn.description}</TableCell>
                        <TableCell className="text-right font-mono tabular-nums text-sm font-bold">
                          {txn.amount_display || `₹${txn.amount.toLocaleString('en-IN')}`}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  No transactions available
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}