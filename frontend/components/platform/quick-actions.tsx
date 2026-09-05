/**
 * Quick Actions — M9-C57 Phase 5
 *
 * Set of action buttons for the dashboard.
 * Each action navigates to the corresponding platform sub-page.
 */

'use client';

import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  AlertCircle,
  Bug,
  Clock,
  FileSearch,
  Gauge,
  Layers,
  ListChecks,
  Shield,
} from 'lucide-react';

interface ActionButtonProps {
  label: string;
  icon: React.ReactNode;
  href: string;
  count?: number;
  variant?: 'default' | 'alert';
  className?: string;
}

function ActionButton({ label, icon, href, count, variant = 'default', className }: ActionButtonProps) {
  const router = useRouter();
  return (
    <button
      onClick={() => router.push(href)}
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-all hover:bg-[var(--surface-interactive)]',
        variant === 'alert'
          ? 'border-red-500/30 hover:border-red-500/50'
          : 'border-[var(--border-subtle)] hover:border-[var(--border-default)]',
        className,
      )}
    >
      <span className={cn('shrink-0', variant === 'alert' ? 'text-red-400' : 'text-[var(--text-secondary)]')}>
        {icon}
      </span>
      <span className="text-sm font-medium text-[var(--text-primary)] flex-1">
        {label}
      </span>
      {count !== undefined && count > 0 && (
        <span className={cn(
          'text-xs font-mono px-2 py-0.5 rounded-full',
          variant === 'alert'
            ? 'bg-red-500/20 text-red-400'
            : 'bg-[var(--surface-raised)] text-[var(--text-secondary)]',
        )}>
          {count}
        </span>
      )}
    </button>
  );
}

interface QuickActionsProps {
  errorCount?: number;
  lastVerification?: string;
  className?: string;
}

export function QuickActions({
  errorCount = 0,
  lastVerification,
  className,
}: QuickActionsProps) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <ActionButton
        label="Diagnose Issues"
        icon={<Bug className="h-4 w-4" />}
        href="/platform/diagnostics"
        variant={errorCount > 0 ? 'alert' : 'default'}
        count={errorCount}
      />
      <ActionButton
        label="Run Verification"
        icon={<ListChecks className="h-4 w-4" />}
        href="/platform/verification"
      />
      <ActionButton
        label="View History"
        icon={<Clock className="h-4 w-4" />}
        href="/platform/history"
        count={lastVerification ? 1 : 0}
      />
      <ActionButton
        label="Inspect Errors"
        icon={<AlertCircle className="h-4 w-4" />}
        href="/platform/errors"
        variant={errorCount > 0 ? 'alert' : 'default'}
        count={errorCount}
      />
      <ActionButton
        label="Architecture Safety"
        icon={<Shield className="h-4 w-4" />}
        href="/platform/architecture"
      />
      <ActionButton
        label="Capabilities"
        icon={<Layers className="h-4 w-4" />}
        href="/platform/capabilities"
      />
      <ActionButton
        label="Change Intelligence"
        icon={<FileSearch className="h-4 w-4" />}
        href="/platform/diagnostics/change"
      />
      <ActionButton
        label="Settings"
        icon={<Gauge className="h-4 w-4" />}
        href="/platform/settings"
      />
    </div>
  );
}
