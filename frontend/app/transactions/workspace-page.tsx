/**
 * Transaction Workspace Page - Stage 3 Transaction Intelligence Workspace
 *
 * Main workspace page component that composes all regions.
 * Uses the capability layer for state management.
 */

'use client';

import { useTransactionCapability } from '@/lib/capabilities/use-transaction-capability';
import { useEvidence } from '@/lib/evidence/use-evidence';
import { TransactionSearch } from '@/components/search/transaction-search';
import { FilterPanel } from '@/components/filters/filter-panel';
import { LoadingSpinner } from '@/components/loading/loading-spinner';
import { ErrorMessage } from '@/components/loading/error-message';
import { EmptyState } from '@/components/loading/empty-state';
import { EvidenceDrawer } from '@/components/evidence/evidence-drawer';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Download, RefreshCw } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';

/**
 * Transaction Workspace Page
 * Composes all workspace regions using the capability layer
 */
export function TransactionWorkspacePage() {
  const capability = useTransactionCapability();
  const evidence = useEvidence();

  // Loading state
  if (capability.loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Error state
  if (capability.error) {
    return (
      <div className="p-6">
        <ErrorMessage
          message={capability.error.message}
          onRetry={capability.refresh}
        />
      </div>
    );
  }

  // Empty state
  if (capability.transactions.length === 0) {
    return (
      <div className="p-6">
        <EmptyState onAction={capability.clearFilters} />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar Region */}
      <div className="border-b bg-background p-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <TransactionSearch
              value={capability.searchQuery}
              onChange={capability.setSearchQuery}
            />
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={capability.refresh}
              disabled={capability.loading}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Filter Panel Region */}
      <FilterPanel
        filters={{
          searchQuery: capability.searchQuery,
          dateFilter: capability.dateFilter,
          categoryFilter: capability.categoryFilter,
          merchantFilter: capability.merchantFilter,
          amountFilter: capability.amountFilter,
          statusFilter: capability.statusFilter as any,
        }}
        onFiltersChange={(filters) => {
          capability.setSearchQuery(filters.searchQuery);
          capability.setDateFilter(filters.dateFilter);
          capability.setCategoryFilter(filters.categoryFilter);
          capability.setMerchantFilter(filters.merchantFilter);
          capability.setAmountFilter(filters.amountFilter);
          capability.setStatusFilter(filters.statusFilter as any);
        }}
      />

      {/* Transaction Table Region */}
      <div className="flex-1 overflow-auto">
        <Card className="border-0 rounded-none">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">Select</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Merchant</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {capability.transactions.map((tx) => (
                  <TableRow
                    key={tx.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => {
                      // Open evidence drawer for this transaction
                      evidence.openEvidence(tx.id, tx.evidence || []);
                    }}
                  >
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={capability.selectedIds.has(tx.id)}
                        onChange={(e) => {
                          e.stopPropagation();
                          capability.toggleSelection(tx.id);
                        }}
                        aria-label={`Select transaction ${tx.id}`}
                      />
                    </TableCell>
                    <TableCell>{tx.date_formatted || tx.date}</TableCell>
                    <TableCell>{tx.description}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="text-xs">
                        {tx.category_name || 'Uncategorized'}
                      </Badge>
                    </TableCell>
                    <TableCell>{tx.merchant_name || '-'}</TableCell>
                    <TableCell
                      className={cn(
                        'text-right font-mono tabular-nums',
                        tx.transaction_type === 'debit' ? 'text-red-600' : 'text-green-600'
                      )}
                    >
                      {formatINR(tx.amount.paise)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        state={evidence}
        onClose={evidence.closeEvidence}
      />
    </div>
  );
}