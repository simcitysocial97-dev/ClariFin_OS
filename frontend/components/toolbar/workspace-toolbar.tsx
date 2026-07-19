/**
 * Workspace Toolbar Component - Stage 3 Transaction Intelligence Workspace
 *
 * Toolbar component for the Transaction Intelligence Workspace.
 */

'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Filter,
  Group,
  SortAsc,
  Download,
  RefreshCw,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface WorkspaceToolbarProps {
  onSearchClick: () => void;
  onFilterToggle: () => void;
  onGroupToggle: () => void;
  onSortToggle: () => void;
  onExport: () => void;
  onRefresh: () => void;
  onSettings: () => void;
  transactionCount: number;
  activeFilterCount: number;
  loading?: boolean;
}

/**
 * Workspace Toolbar Component
 * Displays action buttons and status indicators for the workspace
 */
export function WorkspaceToolbar({
  onSearchClick,
  onFilterToggle,
  onGroupToggle,
  onSortToggle,
  onExport,
  onRefresh,
  onSettings,
  transactionCount,
  activeFilterCount,
  loading = false,
}: WorkspaceToolbarProps) {
  return (
    <div className="flex items-center justify-between gap-4 p-4 border-b bg-background">
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onSearchClick}
          className="flex items-center gap-2"
        >
          <Search className="h-4 w-4" />
          Search
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onFilterToggle}
          className="flex items-center gap-2"
        >
          <Filter className="h-4 w-4" />
          Filter
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-1 text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onGroupToggle}
          className="flex items-center gap-2"
        >
          <Group className="h-4 w-4" />
          Group
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onSortToggle}
          className="flex items-center gap-2"
        >
          <SortAsc className="h-4 w-4" />
          Sort
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">
          {transactionCount} transactions
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={onExport}
          className="flex items-center gap-2"
        >
          <Download className="h-4 w-4" />
          Export
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2"
        >
          <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          Refresh
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onSettings}
          className="flex items-center gap-2"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Button>
      </div>
    </div>
  );
}