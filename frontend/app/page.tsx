'use client';

/**
 * Main Dashboard Page - Personal Finance MVP v1.0.0
 * =====================================================
 * 
 * Simplified dashboard with NO localStorage fallback.
 * Backend is the sole source of truth.
 * 
 * If backend is unavailable, show explicit error UI.
 */

import { useState, useEffect } from 'react';
import { useOverview } from '@/lib/hooks/use-finance-data';
import { useToast } from '@/hooks/use-toast';
import dynamic from 'next/dynamic';
import { QuickStats } from '@/components/dashboard/quick-stats';
import { RecentTransactions } from '@/components/dashboard/recent-transactions';
import { SpendingOverview } from '@/components/dashboard/spending-overview';
import { InsightCards } from '@/components/dashboard/insight-cards';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, TrendingUp, CreditCard, Wallet, AlertCircle } from 'lucide-react';
import { EmptyState } from '@/components/ui/empty-state';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';

const UploadModal = dynamic(
  () => import('@/components/upload/upload-modal').then((mod) => mod.UploadModal)
);

function DashboardContent() {
  const [excludeTransfers, setExcludeTransfers] = useState(false);
  const { data: overview, loading, error, refetch } = useOverview({ exclude_transfers: excludeTransfers });
  const { toast } = useToast();
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  
  // Show error toast if API fails
  useEffect(() => {
    if (error) {
      toast({
        title: 'Error loading dashboard',
        description: error.message,
        variant: 'destructive',
      });
    }
  }, [error, toast]);

  // Open upload modal when upload=true query param is present
  useEffect(() => {
    const shouldUpload = new URLSearchParams(window.location.search).get('upload') === 'true';
    if (shouldUpload) {
      setUploadModalOpen(true);
    }
  }, []);

  // Handle exclude transfers toggle
  const handleExcludeTransfersChange = (checked: boolean) => {
    setExcludeTransfers(checked);
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </div>
          <Skeleton className="h-10 w-36" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
                <Skeleton className="h-3 w-48 mt-2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Error state - BLOCKING (no fallback to localStorage)
  if (error) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Welcome back! Here's your financial overview.
            </p>
          </div>
          <Button onClick={() => setUploadModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Upload Statement
          </Button>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Backend Connection Error</AlertTitle>
          <AlertDescription>
            {error.message}. Please ensure the API server is running at http://localhost:8000
          </AlertDescription>
        </Alert>
        <Card className="p-6">
          <p className="text-gray-600 mb-4">
            The dashboard requires a connection to the backend server to display your financial data.
          </p>
          <p className="text-sm text-gray-500">
            Start the backend with: <code className="bg-gray-100 px-2 py-1 rounded">cd backend && uvicorn src.api:app --reload --port 8000</code>
          </p>
        </Card>
      </div>
    );
  }

  const hasData = overview && overview.transaction_count > 0;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Welcome back! Here's your financial overview.
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Exclude Transfers Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Exclude Transfers</span>
            <Switch
              checked={excludeTransfers}
              onCheckedChange={handleExcludeTransfersChange}
            />
          </div>
          <Button onClick={() => setUploadModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Upload Statement
          </Button>
        </div>
      </div>

      {/* Upload Modal */}
      <UploadModal open={uploadModalOpen} onOpenChange={setUploadModalOpen} />

      {!hasData ? (
        // Empty state
        <div className="max-w-2xl mx-auto space-y-6">
          <EmptyState
            icon={<CreditCard className="h-10 w-10" />}
            title="Welcome to ClariFin"
            description="Get started by uploading your first bank statement. We'll automatically extract your transactions and provide insights into your spending."
            action={{
              label: "Upload Your First Statement",
              onClick: () => setUploadModalOpen(true)
            }}
          />
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
            <Card>
              <CardContent className="pt-6">
                <CreditCard className="h-8 w-8 mx-auto mb-2 text-primary" />
                <p className="text-sm font-medium">Add Cards</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Upload statements from multiple banks
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 text-primary" />
                <p className="text-sm font-medium">Track Spending</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Monitor your expenses by category
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <Wallet className="h-8 w-8 mx-auto mb-2 text-primary" />
                <p className="text-sm font-medium">Save Money</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Identify areas to reduce spending
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        // Dashboard with data
        <>
          <QuickStats 
            totalSpend={overview!.total_spend_display}
            thisMonth={overview!.this_month_display}
            lastMonth={overview!.last_month_display}
            monthChange={overview!.month_change}
            transactionCount={overview!.transaction_count}
            cardCount={overview!.card_count}
            monthlyChart={overview!.monthly_chart}
            aboveBelowAvg={overview!.above_below_avg}
            aboveAvgIsBad={overview!.above_avg_is_bad}
            monthlyAverage={overview!.monthly_average_display}
          />
          
          {/* Behavioral Insights */}
          {overview!.behavioral_insights && overview!.behavioral_insights.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Insights</h2>
              <InsightCards insights={overview!.behavioral_insights} />
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-7">
            <Card className="lg:col-span-4">
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Recent Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <RecentTransactions transactions={overview!.recent_transactions.slice(0, 10)} />
              </CardContent>
            </Card>
            
            <div className="lg:col-span-3 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg font-semibold">Spending by Category</CardTitle>
                </CardHeader>
                <CardContent>
                  <SpendingOverview categoryChart={overview!.category_chart || []} />
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return <DashboardContent />;
}
