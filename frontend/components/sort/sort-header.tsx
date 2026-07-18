/**
 * Sort Header Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for sort header display.
 */

'use client';

import { ArrowUp, ArrowDown } from 'lucide-react';
import type { SortField, SortDirection } from '@/lib/sort/types';

interface SortHeaderProps {
  field: SortField;
  label: string;
  currentField: SortField | null;
  direction: SortDirection;
  onSort: (field: SortField) => void;
}

/**
 * Sort Header Component
 * Displays sortable column header with sort indicator
 */
export function SortHeader({
  field,
  label,
  currentField,
  direction,
  onSort,
}: SortHeaderProps) {
  const isActive = currentField === field;

  return (
    <button
      onClick={() => onSort(field)}
      className="flex items-center gap-1 font-medium hover:text-foreground"
    >
      {label}
      {isActive && (
        direction === 'asc' ? (
          <ArrowUp className="h-3 w-3" />
        ) : (
          <ArrowDown className="h-3 w-3" />
        )
      )}
    </button>
  );
}