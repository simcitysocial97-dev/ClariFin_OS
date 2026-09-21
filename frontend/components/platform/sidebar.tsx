/**
 * Platform Console Sidebar Navigation — M9-C57 Phase 9
 *
 * Adds a persistent left-rail navigation to the platform console.
 * Distinct from the financial AppShell — this is the platform's own nav.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  TestTube,
  Bug,
  History,
  Shield,
  Layers,
  Settings,
  ShieldCheck,
  Zap,
  FileText,
  HeartPulse,
  Terminal,
  GitBranch,
} from 'lucide-react';

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/platform', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/platform/health', label: 'Health', icon: HeartPulse },
  { href: '/platform/verification', label: 'Verification', icon: TestTube },
  { href: '/platform/diagnostics', label: 'Diagnostics', icon: Bug, badge: '5' },
  { href: '/platform/diagnostics/change', label: 'Change Intelligence', icon: Zap },
  { href: '/platform/framework', label: 'Framework', icon: ShieldCheck },
  { href: '/platform/workflows', label: 'Workflows', icon: Terminal },
  { href: '/platform/runs', label: 'Runs', icon: History },
  { href: '/platform/history', label: 'History', icon: History },
  { href: '/platform/errors', label: 'Errors', icon: Shield },
  { href: '/platform/evidence', label: 'Evidence', icon: FileText },
  { href: '/platform/capabilities', label: 'Capabilities', icon: Layers },
  { href: '/platform/architecture', label: 'Architecture', icon: GitBranch },
  { href: '/platform/settings', label: 'Settings', icon: Settings },
];

export function PlatformSidebar() {
  const pathname = usePathname();

  return (
    <nav className="w-48 shrink-0 flex flex-col border-r border-[var(--border-subtle)] bg-[var(--surface-base)]">
      {/* Brand */}
      <div className="px-3 py-3 border-b border-[var(--border-subtle)]">
        <div className="text-xs font-mono text-[var(--text-tertiary)] uppercase tracking-widest">Platform</div>
        <div className="text-sm font-semibold text-[var(--text-primary)] mt-0.5">ClariFin OS</div>
      </div>

      {/* Nav items */}
      <div className="flex-1 overflow-y-auto py-2">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 text-sm transition-colors',
                active
                  ? 'bg-[var(--surface-raised)] text-[var(--text-primary)] border-r-2 border-violet-400'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]',
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate flex-1">{item.label}</span>
              {item.badge && (
                <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-[var(--border-subtle)]">
        <div className="text-xs text-[var(--text-tertiary)] font-mono">v1.0.0</div>
        <div className="text-xs text-[var(--text-tertiary)] font-mono mt-0.5">M9-C57 Band B</div>
      </div>
    </nav>
  );
}
