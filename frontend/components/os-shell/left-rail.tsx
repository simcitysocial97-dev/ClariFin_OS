/**
 * Left Rail - Stage 8E Financial Operating System Shell
 *
 * Navigation rail for the Financial Operating System.
 * Width: 180px (expanded), 56px (collapsed).
 * Uses FinancialIcon, Surface, ScrollRegion from Stage 8E primitives.
 * Navigation driven ONLY from WorkspaceRegistry.
 */

'use client';

import { useState, useMemo, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import { navigationRuntime } from '@/lib/runtime';
import { useShell } from './shell-provider';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { ScrollRegion } from '@/components/primitives/layout/scroll-region';
import { Stack } from '@/components/primitives/layout/stack';
import { cn } from '@/lib/utils';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

// ===== Domain Groups =====
// Derived from workspace registry — never hardcoded.
interface DomainGroup {
  id: string;
  label: string;
  iconName: string;
  workspaces: { name: WorkspaceName; label: string; icon: string; deepLink: string }[];
}

function buildDomainGroups(): DomainGroup[] {
  const all = workspaceRegistry.getAll();
  const groups: DomainGroup[] = [
    {
      id: 'overview',
      label: 'Overview',
      iconName: 'layout-dashboard',
      workspaces: all.filter(w => ['dashboard', 'net-worth', 'cashflow'].includes(w.name)).map(w => ({
        name: w.name,
        label: w.label,
        icon: w.icon ?? 'layout-dashboard',
        deepLink: w.deepLink,
      })),
    },
    {
      id: 'transactions',
      label: 'Transactions',
      iconName: 'receipt',
      workspaces: all.filter(w => ['transactions', 'reconciliation'].includes(w.name)).map(w => ({
        name: w.name,
        label: w.label,
        icon: w.icon ?? 'receipt',
        deepLink: w.deepLink,
      })),
    },
    {
      id: 'accounts',
      label: 'Accounts',
      iconName: 'wallet',
      workspaces: all.filter(w => ['accounts', 'cards', 'loans'].includes(w.name)).map(w => ({
        name: w.name,
        label: w.label,
        icon: w.icon ?? 'wallet',
        deepLink: w.deepLink,
      })),
    },
    {
      id: 'investments',
      label: 'Investments',
      iconName: 'trending-up',
      workspaces: all.filter(w => ['investments'].includes(w.name)).map(w => ({
        name: w.name,
        label: w.label,
        icon: w.icon ?? 'trending-up',
        deepLink: w.deepLink,
      })),
    },
    {
      id: 'intelligence',
      label: 'Intelligence',
      iconName: 'brain',
      workspaces: all.filter(w => ['behaviour', 'forecast'].includes(w.name)).map(w => ({
        name: w.name,
        label: w.label,
        icon: w.icon ?? 'brain',
        deepLink: w.deepLink,
      })),
    },
    {
      id: 'settings',
      label: 'Settings',
      iconName: 'settings',
      workspaces: all.filter(w => ['settings'].includes(w.name)).map(w => ({
        name: w.name,
        label: w.label,
        icon: w.icon ?? 'settings',
        deepLink: w.deepLink,
      })),
    },
  ];
  return groups.filter(g => g.workspaces.length > 0);
}

// ===== Left Rail Component =====
interface LeftRailProps {
  className?: string;
}

export function LeftRail({ className }: LeftRailProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const { performance } = useShell();

  const domainGroups = useMemo(() => buildDomainGroups(), []);

  // Get runtime health
  const cacheStats = useMemo(() => performance.getCacheStats(), [performance]);
  const graphNodes = cacheStats.size; // proxy for health

  // Determine active workspace from path
  const activeWorkspace = useMemo(() => {
    const path = pathname.split('/')[1] || 'dashboard';
    // Map route to workspace name
    const routeMap: Record<string, WorkspaceName> = {
      dashboard: 'dashboard',
      transactions: 'transactions',
      accounts: 'accounts',
      cards: 'cards',
      loans: 'loans',
      investments: 'investments',
      'net-worth': 'net-worth',
      cashflow: 'cashflow',
      behaviour: 'behaviour',
      forecast: 'forecast',
      reconciliation: 'reconciliation',
      settings: 'settings',
    };
    return routeMap[path] ?? 'dashboard';
  }, [pathname]);

  // Navigation history depth indicator
  const navDepth = navigationRuntime.state.currentIndex + 1;

  // Handle workspace navigation — push to history
  const handleWorkspaceNav = useCallback((workspace: WorkspaceName, deepLink: string) => {
    const fullPath = deepLink + window.location.search;
    navigationRuntime.pushPath(fullPath, workspace);
  }, []);

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen flex flex-col',
        'border-r border-[var(--border-default)]',
        'bg-[var(--surface-default)]',
        'transition-all duration-150 ease-out',
        // Mobile: collapsed by default (56px), Desktop: expanded (180px)
        'lg:w-[180px] w-14',
        className,
      )}
    >
      {/* Header */}
      <div
        className={cn(
          'flex items-center border-b border-[var(--border-default)]',
          'h-11 min-h-11',
          collapsed ? 'justify-center px-2' : 'justify-between px-3',
        )}
      >
        {!collapsed && (
          <span className="fin-panel-header truncate text-[var(--text-primary)]">
            ClariFin
          </span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center rounded-[var(--radius-sm)] h-6 w-6 hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="h-3.5 w-3.5" />
          ) : (
            <ChevronLeft className="h-3.5 w-3.5" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <ScrollRegion className="flex-1 px-1 py-1.5">
        <Stack gap={2}>
          {domainGroups.map((group) => (
            <div key={group.id}>
              {/* Group label (collapsed: hidden) */}
              {!collapsed && (
                <div className="px-1.5 py-0.5">
                  <span className="fin-hint uppercase tracking-wider font-semibold">
                    {group.label}
                  </span>
                </div>
              )}

              {/* Workspace links */}
              <Stack gap={0}>
                {group.workspaces.map((ws) => {
                  const isActive = activeWorkspace === ws.name;
                  return collapsed ? (
                    /* Collapsed: icon-only with tooltip via title */
                    <Link
                      key={ws.name}
                      href={ws.deepLink}
                      onClick={() => handleWorkspaceNav(ws.name, ws.deepLink)}
                      title={ws.label}
                      className={cn(
                        'flex items-center justify-center h-8 w-full rounded-[var(--radius-sm)] transition-colors relative',
                        isActive
                          ? 'bg-[var(--surface-selected)] text-[var(--color-selection)]'
                          : 'text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)]',
                      )}
                    >
                      <FinancialIcon name={ws.icon} size={15} />
                      {isActive && (
                        <span className="absolute left-0.5 top-1/2 -translate-y-1/2 w-0.5 h-3.5 rounded-full bg-[var(--color-selection)]" />
                      )}
                    </Link>
                  ) : (
                    /* Expanded: icon + label */
                    <Link
                      key={ws.name}
                      href={ws.deepLink}
                      onClick={() => handleWorkspaceNav(ws.name, ws.deepLink)}
                      className={cn(
                        'flex items-center gap-2 h-7 px-2 rounded-[var(--radius-sm)] transition-colors relative group',
                        isActive
                          ? 'bg-[var(--surface-selected)] text-[var(--text-primary)]'
                          : 'text-[var(--text-secondary)] hover:bg-[var(--surface-interactive)] hover:text-[var(--text-primary)]',
                      )}
                    >
                      <FinancialIcon
                        name={ws.icon}
                        size={13}
                        className={cn(
                          'shrink-0',
                          isActive ? 'text-[var(--color-selection)]' : 'text-[var(--text-tertiary)] group-hover:text-[var(--text-secondary)]',
                        )}
                      />
                      <span className="fin-label text-[var(--fs-sm)] truncate flex-1">{ws.label}</span>
                      {isActive && (
                        <span className="h-1 w-1 rounded-full bg-[var(--color-selection)] shrink-0" />
                      )}
                    </Link>
                  );
                })}
              </Stack>
            </div>
          ))}
        </Stack>
      </ScrollRegion>

      {/* Footer */}
      <div className="border-t border-[var(--border-default)] px-2 py-1.5">
        {collapsed ? (
          <div className="flex flex-col items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-positive-500)]" title="Healthy" />
            <span className="fin-caption text-[9px]" title="Navigation depth">{navDepth}</span>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-positive-500)]" />
              <span className="fin-caption">{graphNodes} nodes</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="fin-caption">Depth: {navDepth}</span>
              <span className="fin-caption">v1.0</span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}