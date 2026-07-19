/**
 * Workspace Toolbar Component - Stage 3 Transaction Intelligence Workspace
 *
 * Toolbar component for the Transaction Intelligence Workspace.
 * Responsive design for mobile and desktop.
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
 * Responsive: stacks on mobile, horizontal on desktop
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
    <div className="flex flex-col sm:flex-row items-center justify-between gap-2 sm:gap-4 p-4 border-b bg-background">
      {/* Left side: Action buttons - wraps on mobile */}
      <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={onSearchClick}
            className="flex items-center gap-2 w-full sm:w-auto"
          >
            <Search className="h-4 w-4" />
            <span className="sm:hidden">Search</span>
            <span className="hidden sm:inline">Search</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onFilterToggle}
            className="flex items-center gap-2 w-full sm:w-auto"
          >
            <Filter className="h-4 w-4" />
            <span className="sm:hidden">Filter</span>
            <span className="hidden sm:inline">Filter</span>
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
            className="flex items-center gap-2 w-full sm:w-auto"
          >
            <Group className="h-4 w-4" />
            <span className="sm:hidden">Group</span>
            <span className="hidden sm:inline">Group</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onSortToggle}
            className="flex items-center gap-2 w-full sm:w-auto"
          >
            <SortAsc className="h-4 w-4" />
            <span className="sm:hidden">Sort</span>
            <span className="hidden sm:inline">Sort</span>
          </Button>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            className="flex items-center gap-2 w-full sm:w-auto"
          >
            <Download className="h-4 w-4" />
            <span className="sm:hidden">Export</span>
            <span className="hidden sm:inline">Export</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center gap-2 w-full sm:w-auto"
          >
            <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
            <span className="sm:hidden">Refresh</span>
            <span className="hidden sm:inline">Refresh</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onSettings}
            className="flex items-center gap-2 w-full sm:w-auto"
          >
            <Settings className="h-4 w-4" />
            <span className="sm:hidden">Settings</span>
            <span className="hidden sm:inline">Settings</span>
          </Button>
        </div>
      </div>

      {/* Right side: Transaction count - responsive text */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground w-full sm:w-auto justify-between sm:justify-end">
        <span className="hidden sm:inline">{transactionCount} transactions</span>
        <span className="sm:hidden">{transactionCount}</span>
      </div>
    </div>
  );
}