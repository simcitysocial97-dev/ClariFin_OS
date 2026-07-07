'use client'

import { formatINR, formatDateDisplay, rupeesToPaise } from '@/lib/utils/format'
import { CheckCircle, XCircle, ArrowLeftRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useConfirmReconciliation, useRejectReconciliation } from '@/lib/hooks/use-reconciliation'
import type { ReconciliationMatch } from '@/lib/hooks/use-reconciliation'

interface ReconciliationMatchCardProps {
  match: ReconciliationMatch
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'bg-green-500'
  if (confidence >= 0.5) return 'bg-amber-500'
  return 'bg-red-500'
}

function getConfidenceLabel(confidence: number): string {
  return `${Math.round(confidence * 100)}%`
}

function getMatchTypeLabel(matchType: string): string {
  switch (matchType) {
    case 'exact':
      return 'Exact match'
    case 'window':
      return 'Within 3 days'
    case 'fuzzy':
      return 'Similar description'
    case 'manual':
      return 'Manual match'
    default:
      return matchType
  }
}

export function ReconciliationMatchCard({ match }: ReconciliationMatchCardProps) {
  const confirmMutation = useConfirmReconciliation()
  const rejectMutation = useRejectReconciliation()

  const isConfirming = confirmMutation.isPending
  const isRejecting = rejectMutation.isPending
  const isActionInProgress = isConfirming || isRejecting

  const handleConfirm = () => {
    confirmMutation.mutate(match.id)
  }

  const handleReject = () => {
    rejectMutation.mutate(match.id)
  }

  // Format amounts (amount is in rupees, convert to paise for formatINR)
  const debitAmountDisplay = formatINR(rupeesToPaise(match.debit_amount_paise))
  const creditAmountDisplay = formatINR(rupeesToPaise(match.credit_amount_paise))

  // Format dates
  const debitDateDisplay = formatDateDisplay(match.debit_date_iso) || match.debit_date
  const creditDateDisplay = formatDateDisplay(match.credit_date_iso) || match.credit_date

  return (
    <Card className="w-full transition-opacity duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <ArrowLeftRight className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">TRANSFER MATCH</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Confidence:</span>
            <div className="flex items-center gap-1">
              <div className="h-2 w-16 bg-muted rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all ${getConfidenceColor(match.match_confidence)}`}
                  style={{ width: `${Math.min(match.match_confidence * 100, 100)}%` }}
                />
              </div>
              <span className="text-xs font-medium">{getConfidenceLabel(match.match_confidence)}</span>
            </div>
          </div>
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {getMatchTypeLabel(match.match_type)}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {/* Transaction Details - Two Columns */}
        <div className="grid grid-cols-2 gap-4">
          {/* Debit Side */}
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">DEBIT</p>
            <p className="text-xs">{debitDateDisplay} • {match.debit_bank}</p>
            <p className="text-sm font-medium truncate" title={match.debit_description}>
              {match.debit_description}
            </p>
            <p className="text-sm font-semibold">{debitAmountDisplay}</p>
          </div>
          
          {/* Credit Side */}
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">CREDIT</p>
            <p className="text-xs">{creditDateDisplay} • {match.credit_bank}</p>
            <p className="text-sm font-medium truncate" title={match.credit_description}>
              {match.credit_description}
            </p>
            <p className="text-sm font-semibold">{creditAmountDisplay}</p>
          </div>
        </div>

        {/* Date Difference */}
        <div className="text-xs text-muted-foreground">
          Date difference: {match.date_diff_days} day{match.date_diff_days !== 1 ? 's' : ''}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          <Button 
            variant="default" 
            size="sm" 
            className="flex-1 bg-green-600 hover:bg-green-700"
            onClick={handleConfirm}
            disabled={isActionInProgress}
          >
            <CheckCircle className="mr-2 h-4 w-4" />
            {isConfirming ? 'Confirming...' : 'Confirm Transfer'}
          </Button>
          
          <Button 
            variant="outline" 
            size="sm" 
            className="flex-1"
            onClick={handleReject}
            disabled={isActionInProgress}
          >
            <XCircle className="mr-2 h-4 w-4" />
            {isRejecting ? 'Rejecting...' : 'Not a Transfer'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}