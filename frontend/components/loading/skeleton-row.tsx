/**
 * Skeleton Row Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for transaction table row loading state.
 */

import { Skeleton } from '@/components/ui/skeleton';
import { TableRow, TableCell } from '@/components/ui/table';

interface SkeletonRowProps {
  columns?: number;
}

/**
 * Skeleton Row Component
 * Displays placeholder rows while loading transaction data
 */
export function SkeletonRow({ columns = 7 }: SkeletonRowProps) {
  return (
    <TableRow>
      {Array.from({ length: columns }).map((_, i) => (
        <TableCell key={i}>
          <Skeleton className="h-4 w-full" />
        </TableCell>
      ))}
    </TableRow>
  );
}

/**
 * Skeleton Table Component
 * Displays multiple skeleton rows for table loading state
 */
export function SkeletonTable({ rows = 5, columns = 7 }: SkeletonRowProps & { rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonRow key={i} columns={columns} />
      ))}
    </>
  );
}