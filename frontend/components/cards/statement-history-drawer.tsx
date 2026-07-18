'use client'

import { formatDateDisplay } from '@/lib/utils/format'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { CheckCircle, AlertCircle, XCircle } from 'lucide-react'
import type { CreditCardSummaryModel } from '@/lib/models/cards'
import type { Statement } from '@/lib/api/client'

interface StatementHistoryDrawerProps {
  card: CreditCardSummaryModel | null
  open: boolean
  onOpenChange: (open: boolean) => void
  statements: Statement[]
}

function getValidationIcon(status: string): React.ReactNode {
  switch (status) {
    case 'exact_match':
      return <CheckCircle className="h-4 w-4 text-green-500" />
    case 'close_match':
      return <AlertCircle className="h-4 w-4 text-amber-500" />
    case 'mismatch':
      return <XCircle className="h-4 w-4 text-red-500" />
    default:
      return <AlertCircle className="h-4 w-4 text-gray-500" />
  }
}

function getValidationLabel(status: string): string {
  switch (status) {
    case 'exact_match':
      return 'Valid'
    case 'close_match':
      return 'Warning'
    case 'mismatch':
      return 'Invalid'
    default:
      return 'Unknown'
  }
}

export function StatementHistoryDrawer({ 
  card, 
  open, 
  onOpenChange, 
  statements 
}: StatementHistoryDrawerProps) {
  if (!card) return null

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Statement History</SheetTitle>
          <SheetDescription>
            {card.bank} • •••• {card.cardLast4}
          </SheetDescription>
        </SheetHeader>
        
        <div className="mt-6">
          {statements.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No statements found for this card.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Period</TableHead>
                  <TableHead>Outstanding</TableHead>
                  <TableHead>Min Due</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Imported</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {statements.map((stmt) => (
                  <TableRow key={stmt.id}>
                    <TableCell className="text-sm">
                      {stmt.period_display || '—'}
                    </TableCell>
                    <TableCell className="text-sm">
                      {stmt.total_due_display}
                    </TableCell>
                    <TableCell className="text-sm">
                      {stmt.min_due_display}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getValidationIcon(stmt.validation_status)}
                        <span className="text-sm">{getValidationLabel(stmt.validation_status)}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {stmt.imported_at ? formatDateDisplay(stmt.imported_at) : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}