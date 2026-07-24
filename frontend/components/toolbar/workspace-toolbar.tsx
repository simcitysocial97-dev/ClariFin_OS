/**
 * Workspace Toolbar Component - Stage 3 Transaction Intelligence Workspace
 *
 * Toolbar component for the Transaction Intelligence Workspace.
 * Responsive design for mobile and desktop.
 * Dark mode support with bg-background classes.
 * Keyboard shortcuts: Ctrl/Cmd + F (search), Ctrl/Cmd + Shift + F (filter),
 * Ctrl/Cmd + G (group), Ctrl/Cmd + S (sort), Ctrl/Cmd + R (refresh)
 */

'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search, Filter, Group, SortAsc, Download, RefreshCw, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ErrorMessage } from '@/components/loading/error-message';

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
  error?: string | null;
  onErrorRetry?: () => void;
  // Customization options
  showSearch?: boolean;
  showFilter?: boolean;
  showGroup?: boolean;
  showSort?: boolean;
  showExport?: boolean;
  showRefresh?: boolean;
  showSettings?: boolean;
}

/**
 * Workspace Toolbar Component
 * Displays action buttons and status indicators for the workspace
 * Responsive: stacks on mobile, horizontal on desktop
 * Dark mode: uses bg-background for proper theme support
 * Accessibility: includes aria-labels and keyboard navigation support
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
  error = null,
  onErrorRetry,
  showSearch = true,
  showFilter = true,
  showGroup = true,
  showSort = true,
  showExport = true,
  showRefresh = true,
  showSettings = true,
}: WorkspaceToolbarProps) {
  return (
    <div
      className="flex flex-col sm:flex-row items-center justify-between gap-2 sm:gap-4 p-4 border-b bg-background dark:bg-background"
      role="toolbar"
      aria-label="Transaction workspace toolbar"
    >
      {/* Left side: Action buttons - wraps on mobile */}
      <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          {showSearch && (
            <Button
              variant="outline"
              size="sm"
              onClick={onSearchClick}
              className="flex items-center gap-2 w-full sm:w-auto"
              aria-label="Search transactions (Ctrl+F)"
            >
              <Search className="h-4 w-4" />
              <span className="sm:hidden">Search</span>
              <span className="hidden sm:inline">Search</span>
            </Button>
          )}
          {showFilter && (
            <Button
              variant="outline"
              size="sm"
              onClick={onFilterToggle}
              className="flex items-center gap-2 w-full sm:w-auto"
              aria-label={`Filter transactions${activeFilterCount > 0 ? ` (${activeFilterCount} active)` : ''} (Ctrl+Shift+F)`}
            >
              <Filter className="h-4 w-4" />
              <span className="sm:hidden">Filter</span>
              <span className="hidden sm:inline">Filter</span>
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs" aria-hidden="true">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          )}
          {showGroup && (
            <Button
              variant="outline"
              size="sm"
              onClick={onGroupToggle}
              className="flex items-center gap-2 w-full sm:w-auto"
              aria-label="Toggle group (Ctrl+G)"
            >
              <Group className="h-4 w-4" />
              <span className="sm:hidden">Group</span>
              <span className="hidden sm:inline">Group</span>
            </Button>
          )}
          {showSort && (
            <Button
              variant="outline"
              size="sm"
              onClick={onSortToggle}
              className="flex items-center gap-2 w-full sm:w-auto"
              aria-label="Sort transactions (Ctrl+S)"
            >
              <SortAsc className="h-4 w-4" />
              <span className="sm:hidden">Sort</span>
              <span className="hidden sm:inline">Sort</span>
            </Button>
          )}
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          {showExport && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExport}
              className="flex items-center gap-2 w-full sm:w-auto"
              aria-label="Export transactions"
            >
              <Download className="h-4 w-4" />
              <span className="sm:hidden">Export</span>
              <span className="hidden sm:inline">Export</span>
            </Button>
          )}
          {showRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={loading}
              className="flex items-center gap-2 w-full sm:w-auto"
              aria-label="Refresh transactions (Ctrl+R)"
            >
              <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
              <span className="sm:hidden">Refresh</span>
              <span className="hidden sm:inline">Refresh</span>
            </Button>
          )}
          {showSettings && (
            <Button
              variant="outline"
              size="sm"
              onClick={onSettings}
              className="flex items-center gap-2 w-full sm:w-auto"
              aria-label="Settings"
            >
              <Settings className="h-4 w-4" />
              <span className="sm:hidden">Settings</span>
              <span className="hidden sm:inline">Settings</span>
            </Button>
          )}
        </div>
      </div>

      {/* Right side: Transaction count - responsive text */}
      <div
        className="flex items-center gap-2 text-sm text-muted-foreground w-full sm:w-auto justify-between sm:justify-end"
        aria-label={`${transactionCount} transactions`}
      >
        {error && (
          <ErrorMessage
            message={error}
            onRetry={onErrorRetry}
            className="mr-2"
          />
        )}
        <span className="hidden sm:inline">{transactionCount} transactions</span>
        <span className="sm:hidden">{transactionCount}</span>
      </div>
    </div>
  );
}
