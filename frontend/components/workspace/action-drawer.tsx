/**
 * Action Drawer Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying bulk action controls.
 */

'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Edit, Trash2, X } from 'lucide-react';

interface ActionDrawerProps {
  selectedCount: number;
  onBulkAction: (action: 'categorize' | 'adjust' | 'delete', payload?: unknown) => Promise<void>;
  onClearSelection: () => void;
}

/**
 * Action Drawer Component
 * Displays bulk action controls for selected transactions
 */
export function ActionDrawer({
  selectedCount,
  onBulkAction,
  onClearSelection,
}: ActionDrawerProps) {
  if (selectedCount === 0) {
    return null;
  }

  return (
    <div className="border-t bg-muted/20 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{selectedCount} selected</Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onBulkAction('categorize')}
            className="flex items-center gap-1"
          >
            <Edit className="h-3 w-3" />
            Categorize
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onBulkAction('adjust')}
            className="flex items-center gap-1"
          >
            Adjust
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onBulkAction('delete')}
            className="flex items-center gap-1"
          >
            <Trash2 className="h-3 w-3" />
            Delete
          </Button>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearSelection}
          className="flex items-center gap-1"
        >
          <X className="h-3 w-3" />
          Clear Selection
        </Button>
      </div>
    </div>
  );
}