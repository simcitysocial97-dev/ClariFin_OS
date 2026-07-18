/**
 * Group Header Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for group header display.
 */

'use client';

import { ChevronDown, ChevronRight } from 'lucide-react';
import type { GroupKey } from '@/lib/groups/types';

interface GroupHeaderProps {
  group: GroupKey;
  isExpanded: boolean;
  onToggle: () => void;
}

/**
 * Group Header Component
 * Displays group summary information with expand/collapse toggle
 */
export function GroupHeader({ group, isExpanded, onToggle }: GroupHeaderProps) {
  return (
    <button
      onClick={onToggle}
      className="flex w-full items-center justify-between p-2 hover:bg-accent text-left"
    >
      <div className="flex items-center gap-2">
        {isExpanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
        <span className="font-medium">{group.label}</span>
      </div>
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>{group.count} transactions</span>
        <span>₹{group.total / 100}</span>
      </div>
    </button>
  );
}