/**
 * SourcesPanel - Sources tab for explainability drawer
 *
 * Renders table of source references.
 * Missing fields are hidden gracefully.
 */

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
} from '@/components/ui/table'
import { SourceCard } from '../components/SourceCard'
import type { Explanation } from '@/lib/explainability'

interface SourcesPanelProps {
  explanation: Explanation
}

/**
 * Display sources as a table
 */
export function SourcesPanel({ explanation }: SourcesPanelProps) {
  const sources = explanation.sources

  if (sources.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No sources available for this metric.
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Type</TableHead>
          <TableHead>ID</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sources.map((source, index) => (
          <SourceCard key={`${source.type}-${source.id ?? index}`} source={source} />
        ))}
      </TableBody>
    </Table>
  )
}