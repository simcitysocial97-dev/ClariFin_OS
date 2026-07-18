/**
 * Selection Checkbox Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for transaction selection checkbox.
 */

'use client';

import { Checkbox } from '@/components/ui/checkbox';
import type { SelectionState } from '@/lib/selection/types';

interface SelectionCheckboxProps {
  transactionId: string;
  selectionState: SelectionState;
  onToggle: (id: string) => void;
}

/**
 * Selection Checkbox Component
 * Displays checkbox for transaction selection
 */
export function SelectionCheckbox({
  transactionId,
  selectionState,
  onToggle,
}: SelectionCheckboxProps) {
  const isSelected = selectionState.selectedIds.has(transactionId);

  return (
    <Checkbox
      checked={isSelected}
      onCheckedChange={() => onToggle(transactionId)}
      aria-label={`Select transaction ${transactionId}`}
    />
  );
}