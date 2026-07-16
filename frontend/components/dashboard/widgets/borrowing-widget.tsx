/**
 * Borrowing Widget - Loans and Credit Cards Summary
 * 
 * Shows what you owe: Loans, Credit Cards, EMI
 */

'use client';
import { Home, CreditCard, AlertCircle } from 'lucide-react';
import { formatINRCompact } from '@/lib/utils/format';
import { useLoans, type Loan } from '@/lib/hooks/use-loans';
import { useCards, type CardsData, type CardSummary } from '@/lib/hooks/use-cards';
import type { HookState } from '@/lib/hooks/use-async-query';

export function BorrowingWidget() {
  const loansResult = useLoans();
  const cardsResult = useCards() as HookState<CardsData>;

  // useLoans returns TanStack Query result
  const loansData = 'data' in loansResult ? loansResult.data : undefined;
  const loansLoading = 'isLoading' in loansResult ? loansResult.isLoading : false;

  const cardsData = cardsResult.data;
  const cardsLoading = cardsResult.loading;

  if ((loansLoading && !loansData) || (cardsLoading && !cardsData)) return null;

  // Calculate totals from the data
  const totalLoanOutstanding = Array.isArray(loansData?.loans) 
    ? loansData.loans.reduce((sum: number, l: Loan) => sum + (l.outstanding_paise || 0), 0)
    : 0;
  
  const totalEMI = Array.isArray(loansData?.loans)
    ? loansData.loans.reduce((sum: number, l: Loan) => sum + (l.emi_paise || 0), 0)
    : 0;

  const totalCardDue = Array.isArray(cardsData?.cards)
    ? cardsData.cards.reduce((sum: number, c: CardSummary) => sum + (c.current_outstanding || 0), 0)
    : 0;

  const hasOverdue = cardsData?.cards?.some((c: CardSummary) => 
    c.payment_due_date && new Date(c.payment_due_date) < new Date()
  );

  return (
    <div className="space-y-4">
      {/* Loans Summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Home className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">Loans</span>
        </div>
        <div className="text-right">
          <p className="font-semibold">{formatINRCompact(totalLoanOutstanding)}</p>
          <p className="text-xs text-muted-foreground">EMI: {formatINRCompact(totalEMI)}/mo</p>
        </div>
      </div>

      {/* Credit Cards Summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CreditCard className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">Credit Cards</span>
        </div>
        <div className="text-right">
          <p className="font-semibold">{formatINRCompact(totalCardDue)}</p>
          {hasOverdue && (
            <p className="text-xs text-red-500 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Due soon
            </p>
          )}
        </div>
      </div>

      {/* Total Borrowing */}
      <div className="border-t pt-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Total Borrowing</span>
          <span className="font-semibold">{formatINRCompact(totalLoanOutstanding + totalCardDue)}</span>
        </div>
      </div>
    </div>
  );
}