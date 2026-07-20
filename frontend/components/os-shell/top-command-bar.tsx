/**
 * Top Command Bar - Stage 8B Workspace Integration & Surface Migration
 *
 * Height: 44px.
 * Contains: Global Search, Command Palette, Quick Actions, Global Filters,
 *           Workspace Breadcrumbs, Selection Count, Simulation Toggle, Keyboard Hint.
 * Metadata-driven: Actions and filters come from WorkspaceRegistry.
 * Uses existing Command Runtime - no duplication.
 */

'use client';

import { useEffect, useCallback, useMemo } from 'react';
import { useWorkspace } from '@/lib/workspace/workspace-context';
import { commandCenterRuntime } from '@/lib/command-center';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import { GlobalSearch } from '@/components/command-center/global-search';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Command,
  Filter,
  GitCompare,
  ChevronRight,
  Search,
  RefreshCw,
  Download,
  Plus,
  Calendar,
  Settings,
  Group,
  SortAsc,
} from 'lucide-react';
import type { GraphNode } from '@/lib/graph';

// ===== Command Icon Mapping =====
const commandIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  search: Search,
  filter: Filter,
  group: Group,
  sort: SortAsc,
  export: Download,
  refresh: RefreshCw,
  settings: Settings,
  add: Plus,
  'date-range': Calendar,
  period: Calendar,
  evidence: Filter,
  simulate: GitCompare,
  schedule: Calendar,
  match: Command,
  skip: Command,
  delete: Command,
  'select-all': Command,
  import: Download,
  clear: Command,
  validate: Command,
  edit: Command,
};

// ===== Top Command Bar Component =====
interface TopCommandBarProps {
  className?: string;
}

export function TopCommandBar({ className }: TopCommandBarProps) {
  const { state } = useWorkspace();

  // Get current workspace registration from registry
  const workspaceRegistration = useMemo(() => {
    return workspaceRegistry.get(state.currentWorkspace);
  }, [state.currentWorkspace]);

  // Handle keyboard shortcuts from registry
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if focus is on an input or select element
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLSelectElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Command palette (global)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        // Command palette is handled by the runtime
        return;
      }

      // Workspace-specific shortcuts
      if (workspaceRegistration?.keyboardShortcuts) {
        const shortcuts = workspaceRegistration.keyboardShortcuts;
        const key = e.key;

        // Check for Ctrl/Cmd + key shortcuts
        for (const [shortcut, command] of Object.entries(shortcuts)) {
          const isModifier = shortcut.startsWith('Ctrl+') || shortcut.startsWith('Cmd+');
          const actualKey = isModifier ? shortcut.replace('Ctrl+', '').replace('Cmd+', '') : shortcut;

          if (isModifier && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === actualKey.toLowerCase()) {
            e.preventDefault();
            handleCommand(command);
            return;
          } else if (!isModifier && e.key === key && !e.ctrlKey && !e.metaKey) {
            // For non-modifier shortcuts (like Escape)
            e.preventDefault();
            handleCommand(command);
            return;
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [workspaceRegistration]);

  // Get selection count from graph runtime
  const selectionCount = commandCenterRuntime.getSelection().node_ids.length;

  // Get active filter count from filter runtime
  const activeFilterCount = commandCenterRuntime.getFilterRuntime()?.getActiveFilterCount(state.currentWorkspace) ?? 0;

  // Build breadcrumbs
  const breadcrumbs = [
    { label: 'ClariFin', href: '/' },
    { label: workspaceRegistration?.label ?? state.currentWorkspace, href: `/${state.currentWorkspace}` },
  ];

  // Handle node selection from search
  const handleNodeSelect = useCallback((node: GraphNode) => {
    // Navigate to the node's workspace
    if (node.deep_link) {
      window.location.href = node.deep_link;
    }
  }, []);

  // Handle workspace commands
  const handleCommand = useCallback((command: string) => {
    // Commands are handled by the workspace's capability hook
    // This is just a placeholder for the runtime to pick up
    const event = new CustomEvent('workspace-command', { detail: { command, workspace: state.currentWorkspace } });
    window.dispatchEvent(event);
  }, [state.currentWorkspace]);

  // Get workspace-specific commands to display
  const workspaceCommands = useMemo(() => {
    if (!workspaceRegistration) return [];
    return workspaceRegistration.supportedCommands.slice(0, 4); // Limit to 4 primary commands
  }, [workspaceRegistration]);

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30 h-44 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60',
        'pl-180', // Account for left rail
        className,
      )}
    >
      <div className="flex h-full items-center justify-between px-4">
        {/* Left: Breadcrumbs */}
        <div className="flex items-center gap-1 text-sm">
          {breadcrumbs.map((crumb, index) => (
            <div key={crumb.href} className="flex items-center gap-1">
              {index > 0 && <ChevronRight className="h-3 w-3 text-muted-foreground" />}
              <span
                className={cn(
                  index === breadcrumbs.length - 1
                    ? 'font-medium'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {crumb.label}
              </span>
            </div>
          ))}
        </div>

        {/* Center: Search and Filters */}
        <div className="flex-1 max-w-2xl mx-4">
          <GlobalSearch
            onNodeSelect={handleNodeSelect}
            className="w-full"
          />
        </div>

        {/* Right: Actions and Status */}
        <div className="flex items-center gap-2">
          {/* Selection Count */}
          {selectionCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {selectionCount} selected
            </Badge>
          )}

          {/* Workspace-specific Commands (metadata-driven) */}
          {workspaceCommands.map((command) => {
            const Icon = commandIcons[command] ?? Command;
            return (
              <Button
                key={command}
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => handleCommand(command)}
                title={command}
              >
                <Icon className="h-4 w-4" />
              </Button>
            );
          })}

          {/* Global Filters (if workspace supports filters) */}
          {workspaceRegistration?.supportedFilters && workspaceRegistration.supportedFilters.length > 0 && (
            <Button variant="ghost" size="icon" className="h-8 w-8" title="Filters">
              <Filter className="h-4 w-4" />
              {activeFilterCount > 0 && (
                <Badge
                  variant="secondary"
                  className="absolute -top-1 -right-1 h-4 w-4 p-0 text-[10px]"
                >
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          )}

          {/* Simulation Toggle */}
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <GitCompare className="h-4 w-4" />
          </Button>

          {/* Command Palette Trigger - uses runtime */}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-xs text-muted-foreground"
          >
            <Command className="h-3 w-3 mr-1" />
            <span className="hidden sm:inline">Cmd+K</span>
          </Button>
        </div>
      </div>
    </header>
  );
}