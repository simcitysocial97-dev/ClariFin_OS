/**
 * Statement History Component - Stage 4 Credit Cards Intelligence Workspace
 *
 * Displays statement history for credit cards in a table format.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency } from '@/lib/utils/format';
import type { CreditCardsViewModel } from '@/types/credit-cards-view-model';

interface StatementHistoryProps {
  creditCards: CreditCardsViewModel | null;
  loading?: boolean;
  error?: Error | null;
}

/**
 * Statement History Component
 */
export function StatementHistory({ creditCards, loading, error }: StatementHistoryProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Statement History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading statement history...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Statement History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-500">Error loading statement history</p>
        </CardContent>
      </Card>
    );
  }

  if (!creditCards || creditCards.statements.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Statement History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No statements found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Statement History</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Card</TableHead>
              <TableHead>Period</TableHead>
              <TableHead>Total Due</TableHead>
              <TableHead>Min Due</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {creditCards.statements.map((stmt) => (
              <TableRow key={stmt.id}>
                <TableCell className="text-sm font-medium">
                  {stmt.card_id}
                </TableCell>
                <TableCell className="text-sm">
                  {stmt.period_from} to {stmt.period_to}
                </TableCell>
                <TableCell className="text-sm">
                  {formatCurrency(stmt.total_due_paise)}
                </TableCell>
                <TableCell className="text-sm">
                  {formatCurrency(stmt.min_due_paise)}
                </TableCell>
                <TableCell className="text-sm capitalize">
                  {stmt.status}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}