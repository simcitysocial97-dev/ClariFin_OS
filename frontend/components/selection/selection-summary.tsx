/**
 * Selection Summary Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying selection summary and actions.
 */

'use client';

import { Button } from '@/components/ui/button';
import { X, CheckSquare } from 'lucide-react';

interface SelectionSummaryProps {
  count: number;
  total: number;
  onClear: () => void;
  onSelectAll?: () => void;
}

/**
 * Selection Summary Component
 * Displays the count of selected transactions and bulk action controls
 */
export function SelectionSummary({
  count,
  total,
  onClear,
  onSelectAll,
}: SelectionSummaryProps) {
  return (
    <div className="border-t bg-muted/20 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {count} of {total} selected
          </span>
          {onSelectAll && count < total && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onSelectAll}
              className="flex items-center gap-1"
            >
              <CheckSquare className="h-3 w-3" />
              Select All
            </Button>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClear}
          className="flex items-center gap-1"
        >
          <X className="h-3 w-3" />
          Clear
        </Button>
      </div>
    </div>
  );
}