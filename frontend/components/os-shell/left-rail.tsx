/**
 * Left Rail - Stage 8A Financial Operating System Shell
 *
 * Navigation rail for the Financial Operating System.
 * Width: 180px.
 * Reads navigation from WorkspaceRegistry - never hardcoded.
 *
 * Domains: Home, Money, Capital, Investments, Forecast, Intelligence, Operations, Automation, Settings
 */

'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import {
  Home,
  Wallet,
  Building2,
  TrendingUp,
  BarChart3,
  Brain,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
  Cog,
} from 'lucide-react';

// ===== Domain Configuration =====
// These are domains, NOT pages. Each expands into registered workspaces.
interface Domain {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  workspacePrefix?: string;
}

const DOMAINS: Domain[] = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'money', label: 'Money', icon: Wallet, workspacePrefix: 'transactions' },
  { id: 'capital', label: 'Capital', icon: Building2, workspacePrefix: 'accounts' },
  { id: 'investments', label: 'Investments', icon: TrendingUp, workspacePrefix: 'investments' },
  { id: 'forecast', label: 'Forecast', icon: BarChart3, workspacePrefix: 'forecast' },
  { id: 'intelligence', label: 'Intelligence', icon: Brain, workspacePrefix: 'behaviour' },
  { id: 'operations', label: 'Operations', icon: Cog, workspacePrefix: 'reconciliation' },
  { id: 'automation', label: 'Automation', icon: Zap, workspacePrefix: 'settings' },
  { id: 'settings', label: 'Settings', icon: Settings, workspacePrefix: 'settings' },
];

// ===== Left Rail Component =====
interface LeftRailProps {
  className?: string;
}

export function LeftRail({ className }: LeftRailProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  // Get workspaces from registry (dynamic, not hardcoded)
  const workspaces = useMemo(() => workspaceRegistry.getAll(), []);

  // Group workspaces by domain
  const workspacesByDomain = useMemo(() => {
    const groups: Record<string, typeof workspaces> = {};
    for (const domain of DOMAINS) {
      if (domain.workspacePrefix) {
        groups[domain.id] = workspaces.filter(w =>
          w.deepLink.startsWith(`/${domain.workspacePrefix}`),
        );
      }
    }
    return groups;
  }, [workspaces]);

  // Determine active domain from current path
  const activeDomain = useMemo(() => {
    const pathParts = pathname.split('/')[1];
    for (const domain of DOMAINS) {
      if (domain.workspacePrefix && pathParts === domain.workspacePrefix) {
        return domain.id;
      }
    }
    if (pathname === '/' || pathname === '/dashboard') return 'home';
    if (pathname === '/settings') return 'settings';
    return null;
  }, [pathname]);

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-300',
        collapsed ? 'w-14' : 'w-180',
        className,
      )}
    >
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex h-14 items-center justify-between border-b px-3">
          {!collapsed && (
            <span className="text-sm font-semibold">ClariFin OS</span>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="ml-auto"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 px-2 py-2">
          <nav className="flex flex-col gap-1">
            {DOMAINS.map(domain => {
              const isActive = activeDomain === domain.id;
              const domainWorkspaces = workspacesByDomain[domain.id] || [];

              return (
                <div key={domain.id}>
                  <Link
                    href={domain.workspacePrefix ? `/${domain.workspacePrefix}` : '/'}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    )}
                  >
                    <domain.icon className="h-4 w-4 flex-shrink-0" />
                    {!collapsed && <span>{domain.label}</span>}
                  </Link>

                  {/* Sub-workspaces */}
                  {!collapsed && domainWorkspaces.length > 0 && (
                    <div className="ml-4 mt-1 flex flex-col gap-0.5">
                      {domainWorkspaces.map(workspace => {
                        const isActiveWorkspace =
                          pathname === workspace.deepLink ||
                          pathname.startsWith(`${workspace.deepLink}/`);
                        return (
                          <Link
                            key={workspace.name}
                            href={workspace.deepLink}
                            className={cn(
                              'flex items-center gap-2 rounded-md px-2 py-1 text-xs font-medium transition-colors',
                              isActiveWorkspace
                                ? 'bg-primary/5 text-primary'
                                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground',
                            )}
                          >
                            <span className="truncate">{workspace.label}</span>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </ScrollArea>

        {/* Footer */}
        <div className="border-t p-2">
          <div className="flex items-center justify-center">
            <span className="text-xs text-muted-foreground">
              v{process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}