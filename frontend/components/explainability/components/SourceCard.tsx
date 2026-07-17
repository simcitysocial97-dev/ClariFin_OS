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
        {source.type ?? '—'}
      </TableCell>
      <TableCell>
        {source.id ?? '—'}
      </TableCell>
      <TableCell>
        {source.name ?? '—'}
      </TableCell>
      <TableCell>
        {source.date ?? '—'}
      </TableCell>
    </TableRow>
  )
}