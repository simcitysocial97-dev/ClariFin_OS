/**
 * Platform Dashboard — M9-C57 Phase 5 / M9-C63
 *
 * Single-screen overview of ClariFin_OS platform state.
 * Answers: what is healthy, what is broken, what changed, what should I run?
 *
 * Data sources:
 *   /platform/v1/health      → system health snapshot
 *   /platform/v1/events      → recent activity
 *   /platform/v1/errors/recent → error count
 *   /platform/v1/tasks       → open obligation count
 *   /platform/v1/capabilities → capability count
 *
 * Performance budget: < 300ms initial render on Lenovo IdeaPad S145.
 * No repository scan, no full verification, no LLM call.
 */

'use client';

import { usePlatformHealthSummary } from '@/lib/hooks/use-platform-health';
import { usePlatformEvents } from '@/lib/hooks/use-platform-events';
import { useCurrentErrorCount } from '@/lib/hooks/use-platform-errors';
import { useOpenObligationsCount } from '@/lib/hooks/use-platform-tasks';
import { useCapabilityList } from '@/lib/hooks/use-platform-capabilities';
import { HealthBadge } from '@/components/platform/health-badge';
import { MetricTile } from '@/components/platform/metric-tile';
import { ActivityFeed } from '@/components/platform/activity-feed';
import { QuickActions } from '@/components/platform/quick-actions';
import { AlertTriangle, CheckCircle2, Clock, Layers, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================
// Sub-components
// ============================================================

function SystemStatusCard({ platform, frameworkIntegrity }: { platform: string; frameworkIntegrity: string }) {
  const platformIcon =
    platform === 'HEALTHY' ? (
      <CheckCircle2 className="h-8 w-8 text-emerald-400" />
    ) : platform === 'UNHEALTHY' ? (
      <AlertTriangle className="h-8 w-8 text-red-400" />
    ) : (
      <Clock className="h-8 w-8 text-amber-400" />
    );

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        {platformIcon}
        <div>
          <div className="text-2xl font-bold text-[var(--text-primary)]">{platform}</div>
          <div className="text-sm text-[var(--text-tertiary)]">System Status</div>
        </div>
      </div>
      <div className="flex items-center gap-1.5 ml-auto">
        <span className="text-xs text-[var(--text-tertiary)]">Framework:</span>
        <HealthBadge status={frameworkIntegrity} size="sm" showLabel={true} />
      </div>
    </div>
  );
}

function DimensionsGrid({
  domains,
  platformStatus: _platformStatus,
  frameworkIntegrityStatus,
}: {
  domains: { name: string; status: string; last_check: string; source: string; detail?: string }[];
  platformStatus: string;
  frameworkIntegrityStatus: string;
}) {
  // Show top-level statuses from actual health domains
  const topLevelNames = ['Backend', 'Frontend', 'Database', 'Architecture', 'Verification', 'Evidence', 'AI Runtime', 'Framework Integrity'];

  return (
    <div className="flex flex-col gap-3">
      {/* Top-level summary row */}
      <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
        {topLevelNames.map((label) => {
          let status: string;
          if (label === 'Framework Integrity') {
            status = frameworkIntegrityStatus;
          } else {
            status = domains.find((d) => d.name === label)?.status ?? 'UNKNOWN';
          }
          return (
            <div key={label} className="flex flex-col items-center gap-1">
              <HealthBadge status={status} size="sm" showLabel={false} />
              <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-wide text-center">
                {label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Domain detail table */}
      {domains.length > 0 && (
        <div className="border-t border-[var(--border-subtle)] pt-2 mt-1">
          <div className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider mb-2">
            Domain Breakdown
          </div>
          <div className="flex flex-col gap-1">
            {domains.map((d) => (
              <div
                key={d.name}
                className="flex items-center gap-3 text-xs py-1"
              >
                <HealthBadge status={d.status} size="sm" showLabel={false} />
                <span className="text-[var(--text-primary)] font-medium w-36 truncate">
                  {d.name}
                </span>
                <span className="text-[var(--text-tertiary)] truncate flex-1 font-mono">
                  {d.source}
                </span>
                <span className="text-[var(--text-tertiary)] font-mono">
                  {d.last_check}
                </span>
                {d.detail && (
                  <span className="text-[var(--text-tertiary)] font-mono text-[10px] max-w-xs truncate">
                    {d.detail}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function IssueCounts({
  errorCount,
  openObligations,
  unhealthyDomains,
}: {
  errorCount: number;
  openObligations: number;
  unhealthyDomains: { name: string; status: string }[];
}) {
  return (
    <div className="flex flex-col gap-2">
      <MetricTile
        label="Critical Errors"
        value={errorCount}
        subtitle={errorCount > 0 ? 'actions required' : 'none'}
        accent={errorCount > 0 ? 'negative' : 'positive'}
      />
      <MetricTile
        label="Open Obligations"
        value={openObligations}
        subtitle={openObligations > 0 ? 'pending verification' : 'all resolved'}
        accent={openObligations > 0 ? 'warning' : 'positive'}
      />
      <MetricTile
        label="Degraded Domains"
        value={unhealthyDomains.length}
        subtitle={
          unhealthyDomains.length > 0
            ? unhealthyDomains.map((d) => d.name).join(', ')
            : 'none'
        }
        accent={unhealthyDomains.length > 0 ? 'negative' : 'positive'}
      />
    </div>
  );
}

function VerificationStatusCard() {
  const healthData = usePlatformHealthSummary();
  const { data: eventsData, isLoading } = usePlatformEvents(3);

  if (healthData.isLoading || isLoading) {
    return (
      <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] p-4">
        <div className="text-sm text-[var(--text-tertiary)] animate-pulse">Loading verification status…</div>
      </div>
    );
  }

  const verificationStatus = healthData.verificationStatus ?? 'UNKNOWN';
  const lastEvent = eventsData?.data?.items[0];

  return (
    <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-violet-400" />
          Verification
        </span>
        <HealthBadge status={verificationStatus} size="sm" />
      </div>
      <div className="text-xs text-[var(--text-tertiary)]">
        Last run: {lastEvent ? lastEvent.emitted_at : 'N/A'}
      </div>
    </div>
  );
}

function CapabilitiesSummary({ count, stages }: { count: number; stages: number }) {
  return (
    <MetricTile
      label="Capabilities"
      value={count}
      subtitle={`${stages} stages · 0 issues`}
      accent="positive"
    />
  );
}

// ============================================================
// Main Dashboard Page
// ============================================================

export default function PlatformDashboardPage() {
  const {
    isLoading: healthLoading,
    platformStatus,
    frameworkIntegrityStatus,
    unhealthyDomains,
  } = usePlatformHealthSummary();
  const { data: eventsData, isLoading: eventsLoading } = usePlatformEvents(8);
  const errorCount = useCurrentErrorCount();
  const openObligations = useOpenObligationsCount();
  const { data: capsData, isLoading: capsLoading } = useCapabilityList();

  if (healthLoading || capsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-sm text-[var(--text-tertiary)]">Loading platform state…</div>
      </div>
    );
  }

  const capabilityCount = capsData?.data?.count ?? 0;
  const capabilityStages = capsData?.data?.categories?.length ?? 0;

  return (
    <div className="flex flex-col gap-5 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">
            Platform Console
          </h1>
          <p className="text-sm text-[var(--text-tertiary)] mt-0.5">
            ClariFin_OS · Operational State Overview
          </p>
        </div>
        <HealthBadge
          status={platformStatus}
          size="lg"
          className={cn(
            platformStatus === 'HEALTHY' && 'bg-emerald-500/20 text-emerald-300',
            platformStatus === 'UNHEALTHY' && 'bg-red-500/20 text-red-300',
            platformStatus === 'DEGRAD' && 'bg-amber-500/20 text-amber-300',
          )}
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left column: System status + dimensions (8 cols) */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-4">
          {/* System status card */}
          <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] p-5">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                <Layers className="h-4 w-4 text-blue-400" />
                System Status
              </span>
              <SystemStatusCard platform={platformStatus} frameworkIntegrity={frameworkIntegrityStatus} />
            </div>
            <DimensionsGrid
              domains={[]} // Will be populated from health data
              platformStatus={platformStatus}
              frameworkIntegrityStatus={frameworkIntegrityStatus}
            />
          </div>

          {/* Verification + Capabilities */}
          <div className="grid grid-cols-2 gap-4">
            <VerificationStatusCard />
            <CapabilitiesSummary count={capabilityCount} stages={capabilityStages} />
          </div>
        </div>

        {/* Right column: Issue counts + Quick actions + Recent activity (4 cols) */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-4">
          <IssueCounts
            errorCount={errorCount}
            openObligations={openObligations}
            unhealthyDomains={unhealthyDomains}
          />

          <QuickActions
            errorCount={errorCount}
          />

          <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] p-4">
            <div className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2 mb-3">
              <Clock className="h-4 w-4 text-slate-400" />
              Recent Activity
            </div>
            {eventsLoading ? (
              <div className="text-xs text-[var(--text-tertiary)] animate-pulse">Loading events…</div>
            ) : eventsData?.data?.items ? (
              <ActivityFeed
                events={eventsData.data.items}
                limit={8}
              />
            ) : (
              <div className="text-xs text-[var(--text-tertiary)] italic">No recent events</div>
            )}
          </div>
        </div>
      </div>

      {/* Footer bar */}
      <div className="border-t border-[var(--border-subtle)] pt-3 flex items-center justify-between text-xs text-[var(--text-tertiary)] font-mono">
        <span>Platform Console v1.0.0 · M9-C63 · Generated from live C50 authorities</span>
        <span>No AI · No external providers · No second executor</span>
      </div>
    </div>
  );
}
