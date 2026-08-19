/**
 * Top Command Bar - Stage 8B Navigation Experience
 *
 * Height: 44px.
 * Contains: back/forward navigation, breadcrumbs, workspace title, global search,
 *           selection summary, active filters, workspace actions.
 * Navigation driven by NavigationRuntime and WorkspaceRuntime.
 * Breadcrumbs derived from navigation history.
 */

'use client';

import { useMemo, useCallback, useEffect, useState } from 'react';
import { useWorkspace } from '@/lib/workspace/workspace-context';
import { commandCenterRuntime } from '@/lib/command-center';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import { navigationRuntime as navRuntime } from '@/lib/runtime';
import { GlobalSearch } from '@/components/command-center/global-search';
import { CompactToolbar, ToolbarButton, ToolbarSeparator } from '@/components/primitives/toolbar-primitive/compact-toolbar';
import { FinancialBadge } from '@/components/primitives/badge-semantic/financial-badge';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { Kbd } from '@/components/primitives/kbd/kbd';
import { cn } from '@/lib/utils';
import { ChevronRight, ArrowLeft, ArrowRight } from 'lucide-react';
import type { GraphNode } from '@/lib/graph';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

// ===== Breadcrumb Entry =====
interface BreadcrumbEntry {
  label: string;
  workspaceId?: WorkspaceName;
  route?: string;
  timestamp?: number;
}

// ===== Top Command Bar =====
interface TopCommandBarProps {
  className?: string;
}

export function TopCommandBar({ className }: TopCommandBarProps) {
  const { state } = useWorkspace();

  const [navHistory, setNavHistory] = useState<{
    entries: BreadcrumbEntry[];
    currentIndex: number;
  }>({ entries: [], currentIndex: -1 });

  // Sync with navigation runtime
  useEffect(() => {
    const updateFromNav = () => {
      const navState = navRuntime.state;
      const entries: BreadcrumbEntry[] = navState.history.map(h => ({
        label: h.workspace
          ? (workspaceRegistry.get(h.workspace as WorkspaceName)?.label ?? h.workspace)
          : h.path,
        workspaceId: h.workspace as WorkspaceName | undefined,
        route: h.path,
        timestamp: h.timestamp,
      }));
      setNavHistory({ entries, currentIndex: navState.currentIndex });
    };

    updateFromNav();
    const unsub = navRuntime.subscribe(updateFromNav);
    return unsub;
  }, []);

  // Also watch workspace runtime for title updates
  const workspaceRegistration = useMemo(() => {
    return workspaceRegistry.get(state.currentWorkspace);
  }, [state.currentWorkspace]);

  // Get runtime data
  const selectionCount = commandCenterRuntime.getSelection().node_ids.length;
  const activeFilterCount = commandCenterRuntime.getFilterRuntime()?.getActiveFilterCount(state.currentWorkspace) ?? 0;

  // Build breadcrumb trail from navigation history
  const breadcrumbs = useMemo(() => {
    const crumbs: BreadcrumbEntry[] = [{ label: 'ClariFin' }];

    // Add current workspace
    const currentEntry = navHistory.entries[navHistory.currentIndex];
    if (currentEntry) {
      crumbs.push(currentEntry);
    } else {
      crumbs.push({
        label: workspaceRegistration?.label ?? state.currentWorkspace,
        workspaceId: state.currentWorkspace,
        route: `/${state.currentWorkspace}`,
      });
    }

    return crumbs;
  }, [navHistory, workspaceRegistration, state.currentWorkspace]);

  const handleBack = useCallback(() => {
    const entry = navRuntime.goBack();
    if (entry) {
      window.location.href = entry.path;
    }
  }, []);

  const handleForward = useCallback(() => {
    const entry = navRuntime.goForward();
    if (entry) {
      window.location.href = entry.path;
    }
  }, []);

  const handleBreadcrumbClick = useCallback((route?: string, workspaceId?: WorkspaceName) => {
    if (route) {
      window.location.href = route;
    } else if (workspaceId) {
      const reg = workspaceRegistry.get(workspaceId);
      if (reg?.deepLink) {
        window.location.href = reg.deepLink;
      }
    }
  }, []);

  const handleNodeSelect = useCallback((node: GraphNode) => {
    if (node.deep_link) {
      window.location.href = node.deep_link;
    }
  }, []);

  const handleCommand = useCallback((command: string) => {
    const event = new CustomEvent('workspace-command', {
      detail: { command, workspace: state.currentWorkspace },
    });
    window.dispatchEvent(event);
  }, [state.currentWorkspace]);

  // Workspace commands to display
  const workspaceCommands = useMemo(() => {
    if (!workspaceRegistration) return [];
    return workspaceRegistration.supportedCommands.slice(0, 5);
  }, [workspaceRegistration]);

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30',
        'h-11 min-h-11',
        'border-b border-[var(--border-default)]',
        'bg-[var(--surface-default)]',
        // Mobile: full width, Desktop: offset by left rail
        'left-0 w-full',
        'lg:left-[180px] lg:w-auto lg:w-[calc(100%-180px)]',
        'flex items-center',
        className,
      )}
    >
      <div className="flex h-full w-full items-center gap-1.5 px-2">
        {/* Left: Navigation Controls + Breadcrumbs */}
        <div className="flex items-center gap-1 min-w-0 shrink-0">
          {/* Back button */}
          <button
            onClick={handleBack}
            disabled={!navRuntime.canGoBack}
            className={cn(
              'flex items-center justify-center rounded-[var(--radius-sm)] h-6 w-6 shrink-0',
              'transition-colors',
              navRuntime.canGoBack
                ? 'text-[var(--text-secondary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)]'
                : 'text-[var(--text-disabled)] cursor-not-allowed',
            )}
            aria-label="Navigate back"
            title="Back (Alt+ArrowLeft)"
          >
            <ArrowLeft className="h-3 w-3" />
          </button>

          {/* Forward button */}
          <button
            onClick={handleForward}
            disabled={!navRuntime.canGoForward}
            className={cn(
              'flex items-center justify-center rounded-[var(--radius-sm)] h-6 w-6 shrink-0',
              'transition-colors',
              navRuntime.canGoForward
                ? 'text-[var(--text-secondary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)]'
                : 'text-[var(--text-disabled)] cursor-not-allowed',
            )}
            aria-label="Navigate forward"
            title="Forward (Alt+ArrowRight)"
          >
            <ArrowRight className="h-3 w-3" />
          </button>

          {/* Separator */}
          <div className="h-4 w-px bg-[var(--border-default)] mx-0.5 shrink-0" />

          {/* Breadcrumbs */}
          <div className="flex items-center gap-1 min-w-0 shrink-0">
            {breadcrumbs.map((crumb, index) => (
              <div key={`${crumb.label}-${index}`} className="flex items-center gap-1 min-w-0">
                {index > 0 && (
                  <ChevronRight className="h-2.5 w-2.5 text-[var(--text-tertiary)] shrink-0" />
                )}
                {index < breadcrumbs.length - 1 ? (
                  <button
                    onClick={() => handleBreadcrumbClick(crumb.route, crumb.workspaceId)}
                    className="fin-caption text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors truncate max-w-[120px]"
                    aria-label={`Navigate to ${crumb.label}`}
                  >
                    {crumb.label}
                  </button>
                ) : (
                  <span className="fin-label font-medium text-[var(--text-primary)] truncate max-w-[160px]">
                    {crumb.label}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Center: Global Search */}
        <div className="flex-1 max-w-sm mx-1">
          <GlobalSearch
            onNodeSelect={handleNodeSelect}
            className="w-full"
          />
        </div>

        {/* Right: Status + Actions */}
        <CompactToolbar size="sm" className="shrink-0">
          {/* Selection count */}
          {selectionCount > 0 && (
            <FinancialBadge semantic="info" variant="outline" className="text-[9px] px-1 py-0">
              {selectionCount} sel
            </FinancialBadge>
          )}

          {/* Active filter count */}
          {activeFilterCount > 0 && (
            <FinancialBadge semantic="warning" variant="outline" className="text-[9px] px-1 py-0">
              {activeFilterCount} flt
            </FinancialBadge>
          )}

          <ToolbarSeparator />

          {/* Workspace actions */}
          {workspaceCommands.map((command) => (
            <ToolbarButton
              key={command}
              icon={() => <FinancialIcon name={command} size={13} />}
              label={command.charAt(0).toUpperCase() + command.slice(1)}
              onClick={() => handleCommand(command)}
            />
          ))}

          <ToolbarSeparator />

          {/* Cmd+K hint */}
          <div className="flex items-center gap-0.5 px-1 text-[9px] text-[var(--text-tertiary)]">
            <Kbd keys={['cmd', 'K']} size="sm" />
          </div>
        </CompactToolbar>
      </div>
    </header>
  );
}
