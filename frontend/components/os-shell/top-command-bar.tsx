/**
 * Top Command Bar - Stage 8E Financial Operating System Shell
 *
 * Height: 44px.
 * Contains: breadcrumbs, workspace title, global search, selection summary,
 *           active filters, workspace actions.
 * Metadata-driven from WorkspaceRegistry.
 * Uses CompactToolbar, FinancialBadge, FinancialIcon, Kbd.
 */

'use client';

import { useMemo, useCallback } from 'react';
import { useWorkspace } from '@/lib/workspace/workspace-context';
import { commandCenterRuntime } from '@/lib/command-center';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import { GlobalSearch } from '@/components/command-center/global-search';
import { CompactToolbar, ToolbarButton, ToolbarSeparator } from '@/components/primitives/toolbar-primitive/compact-toolbar';
import { FinancialBadge } from '@/components/primitives/badge-semantic/financial-badge';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { Kbd } from '@/components/primitives/kbd/kbd';
import { cn } from '@/lib/utils';
import { ChevronRight } from 'lucide-react';
import type { GraphNode } from '@/lib/graph';

// ===== Top Command Bar =====
interface TopCommandBarProps {
  className?: string;
}

export function TopCommandBar({ className }: TopCommandBarProps) {
  const { state } = useWorkspace();

  // Get workspace registration
  const workspaceRegistration = useMemo(() => {
    return workspaceRegistry.get(state.currentWorkspace);
  }, [state.currentWorkspace]);

  // Get runtime data
  const selectionCount = commandCenterRuntime.getSelection().node_ids.length;
  const activeFilterCount = commandCenterRuntime.getFilterRuntime()?.getActiveFilterCount(state.currentWorkspace) ?? 0;

  // Breadcrumbs
  const breadcrumbs = [
    { label: 'ClariFin' },
    { label: workspaceRegistration?.label ?? state.currentWorkspace },
  ];

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
        'pl-[180px]',
        'flex items-center',
        className,
      )}
    >
      <div className="flex h-full w-full items-center gap-2 px-3">
        {/* Left: Breadcrumbs */}
        <div className="flex items-center gap-1 text-sm min-w-0 shrink-0">
          {breadcrumbs.map((crumb, index) => (
            <div key={crumb.label} className="flex items-center gap-1">
              {index > 0 && (
                <ChevronRight className="h-3 w-3 text-[var(--text-tertiary)]" />
              )}
              <span
                className={cn(
                  index === breadcrumbs.length - 1
                    ? 'fin-label font-medium text-[var(--text-primary)]'
                    : 'fin-caption',
                )}
              >
                {crumb.label}
              </span>
            </div>
          ))}
        </div>

        {/* Center: Global Search */}
        <div className="flex-1 max-w-md mx-2">
          <GlobalSearch
            onNodeSelect={handleNodeSelect}
            className="w-full"
          />
        </div>

        {/* Right: Status + Actions */}
        <CompactToolbar size="sm" className="shrink-0">
          {/* Selection count */}
          {selectionCount > 0 && (
            <FinancialBadge semantic="info" variant="outline" className="text-[10px] px-1.5">
              {selectionCount} selected
            </FinancialBadge>
          )}

          {/* Active filter count */}
          {activeFilterCount > 0 && (
            <FinancialBadge semantic="warning" variant="outline" className="text-[10px] px-1.5">
              {activeFilterCount} filters
            </FinancialBadge>
          )}

          <ToolbarSeparator />

          {/* Workspace actions */}
          {workspaceCommands.map((command) => (
            <ToolbarButton
              key={command}
              icon={() => <FinancialIcon name={command} size={14} />}
              label={command.charAt(0).toUpperCase() + command.slice(1)}
              onClick={() => handleCommand(command)}
            />
          ))}

          <ToolbarSeparator />

          {/* Timeline toggle placeholder */}
          <ToolbarButton
            icon={() => <FinancialIcon name="simulate" size={14} />}
            label="Simulate"
          />

          {/* Cmd+K hint */}
          <div className="flex items-center gap-1 px-1.5 text-[10px] text-[var(--text-tertiary)]">
            <Kbd keys={['cmd', 'K']} size="sm" />
          </div>
        </CompactToolbar>
      </div>
    </header>
  );
}