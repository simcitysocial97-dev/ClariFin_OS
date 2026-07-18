/**
 * Borrowing Widget - Loans and Credit Cards Summary
 * 
 * Shows what you owe: Loans, Credit Cards, EMI
 */

'use client'
import { Home, CreditCard } from 'lucide-react'
import { formatINRCompact } from '@/lib/utils/format'
import { useLoans } from '@/lib/hooks/use-loans'
import { useCards } from '@/lib/hooks/use-cards'

export function BorrowingWidget() {
  const { data: loansData, isLoading: loansLoading } = useLoans()
  const { data: cardsData, isLoading: cardsLoading } = useCards()

  if ((loansLoading && !loansData) || (cardsLoading && !cardsData)) return null

  // Calculate totals from the data
  const totalLoanOutstanding = loansData?.loans.reduce(
    (sum, l) => sum + (l.outstandingPaise ?? 0), 
    0
  ) ?? 0
  
  const totalEMI = loansData?.totalMonthlyEmiPaise ?? 0

  const totalCardDue = cardsData?.cards.reduce(
    (sum, c) => sum + c.currentOutstandingPaise, 
    0
  ) ?? 0

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
  )
}