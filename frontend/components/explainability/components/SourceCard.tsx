/**
 * SourceCard - Display a single source reference
 *
 * Renders the canonical provenance model.
 * Missing fields are hidden gracefully.
 */

import { TableRow, TableCell } from '@/components/ui/table'
import type { SourceReference } from '@/lib/explainability'

interface SourceCardProps {
  source: SourceReference
}

/**
 * Display a single source reference as a table row
 */
export function SourceCard({ source }: SourceCardProps) {
  return (
    <TableRow>
      <TableCell className="font-mono text-xs">
        {source.sourceType ?? '—'}
      </TableCell>
      <TableCell>
        {source.recordId ?? source.statementId ?? source.transactionId ?? '—'}
      </TableCell>
      <TableCell>
        {source.function ?? '—'}
      </TableCell>
      <TableCell>
        {source.file ?? '—'}
      </TableCell>
      <TableCell>
        {source.router ?? '—'}
      </TableCell>
      <TableCell>
        {source.repository ?? '—'}
      </TableCell>
    </TableRow>
  )
}