/**
 * Platform Errors Page — M9-C57 Phase 9A
 *
 * Error Observatory: current, recent, recurring, frequency by layer.
 * Data source: /platform/v1/errors/current|recent|recurring|frequency.
 */

'use client';

import { useEffect, useState, useTransition } from 'react';
import { usePlatformErrors } from '@/lib/hooks/use-platform-errors';
import { usePlatformHealth } from '@/lib/hooks/use-platform-health';
import { AlertTriangle, Activity, Filter, Gauge, Layers, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

type Tab = 'current' | 'recent' | 'recurring' | 'frequency';

export default function ErrorsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('current');
  const { data: healthData } = usePlatformHealth();

  const currentQuery = usePlatformErrors('current');
  const recentQuery = usePlatformErrors('recent');
  const recurringQuery = usePlatformErrors('recurring');

  const activeData =
    activeTab === 'current'
      ? currentQuery.data
      : activeTab === 'recent'
        ? recentQuery.data
        : recurringQuery.data;

  const activeItems = activeData?.data?.items ?? [];
  const activeCount = activeData?.data?.count ?? 0;

  // Frequency tab: fetch once on mount.
  const [frequencyData, setFrequencyData] = useState<{
    total: number;
    buckets: { code: string; layer: string; count: number }[];
  } | null>(null);
  const [_freqLoading, _setFreqLoading] = useState(false);
  const [_isPending, startTransition] = useTransition();

useEffect(() => {
    if (activeTab !== 'frequency') return;
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    startTransition(() => {
      _setFreqLoading(true);
    });
    fetch('/platform/v1/errors/frequency')
      .then((r) => r.json())
      .then((json: { data: { total: number; buckets: { code: string; layer: string; count: number }[] } }) => {
        if (!cancelled) {
          startTransition(() => {
            setFrequencyData(json.data);
            _setFreqLoading(false);
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          startTransition(() => {
            setFrequencyData({ total: 0, buckets: [] });
            _setFreqLoading(false);
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [activeTab]);

  const tabs: { key: Tab; label: string }[] = [
    { key: 'current', label: 'Current' },
    { key: 'recent', label: 'Recent' },
    { key: 'recurring', label: 'Recurring' },
    { key: 'frequency', label: 'Frequency' },
  ];

  return (
    <div className="flex flex-col gap-4 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            Error Observatory
          </h1>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
            Platform-level error aggregation · sourced from integrity checks + open obligations
          </p>
        </div>
        <span className={cn(
          'text-sm font-semibold px-3 py-1 rounded-full border',
          activeCount > 0
            ? 'border-red-500/30 bg-red-500/10 text-red-400'
            : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
        )}>
          {activeCount > 0 ? `${activeCount} active` : 'No active errors'}
        </span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[var(--border-subtle)]">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === tab.key
                ? 'border-red-400 text-red-400'
                : 'border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]',
            )}
          >
            {tab.label}
            {tab.key !== 'frequency' && activeData?.data?.count !== undefined && (
              <span className="ml-2 text-xs opacity-60">{activeData.data.count}</span>
            )}
            {tab.key === 'frequency' && frequencyData && (
              <span className="ml-2 text-xs opacity-60">{frequencyData.total}</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'frequency' ? (
        <FrequencyPanel data={frequencyData} loading={_freqLoading} />
      ) : (
        <ErrorTable
          items={activeItems}
          loading={
            activeTab === 'current'
              ? currentQuery.isLoading
              : activeTab === 'recent'
                ? recentQuery.isLoading
                : recurringQuery.isLoading
          }
          window={
            activeTab === 'current' ? '1h' : activeTab === 'recent' ? '24h' : '7d'
          }
        />
      )}

      {/* Footer info */}
      <div className="text-xs text-[var(--text-tertiary)] border-t border-[var(--border-subtle)] pt-2 flex items-center gap-2">
        <Gauge className="h-3 w-3" />
        <span>Sourced from C50 EvidenceIntegrityReport + open obligation set · no log parsing</span>
        <span className="ml-auto">Verification: {healthData?.data?.verification ?? 'UNKNOWN'}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function ErrorTable({
  items,
  loading,
  window: windowLabel,
}: {
  items: { id: string; code: string; layer: string; message: string; occurrences: number; affected_workflow?: string | null }[];
  loading: boolean;
  window: string;
}) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)] py-8">
        <RefreshCw className="h-4 w-4 animate-spin" />
        Loading errors…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-12 text-[var(--text-tertiary)]">
        <Activity className="h-8 w-8 opacity-40" />
        <span className="text-sm">No errors in this window</span>
        <span className="text-xs">Window: {windowLabel}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs text-[var(--text-tertiary)] flex items-center gap-2">
        <Filter className="h-3 w-3" />
        Showing {items.length} error(s) · window: {windowLabel}
      </div>
      <div className="border border-[var(--border-subtle)] rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border-subtle)] bg-[var(--surface-raised)]">
              <th className="text-left px-3 py-2 text-xs font-mono text-[var(--text-tertiary)]">Code</th>
              <th className="text-left px-3 py-2 text-xs font-mono text-[var(--text-tertiary)]">Layer</th>
              <th className="text-left px-3 py-2 text-xs font-mono text-[var(--text-tertiary)]">Message</th>
              <th className="text-right px-3 py-2 text-xs font-mono text-[var(--text-tertiary)]">Occurrences</th>
              <th className="text-left px-3 py-2 text-xs font-mono text-[var(--text-tertiary)] w-48">Workflow</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className={cn(
                'border-b border-[var(--border-subtle)] last:border-0 hover:bg-[var(--surface-interactive)] transition-colors',
                item.code === 'INTEGRITY_FAILED' ? 'bg-red-500/5' : item.code === 'OBLIGATION_OPEN' ? 'bg-amber-500/5' : '',
              )}>
                <td className="px-3 py-2 font-mono text-xs">
                  <span className={cn(
                    'px-1.5 py-0.5 rounded text-xs',
                    item.code === 'INTEGRITY_FAILED' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400',
                  )}>
                    {item.code}
                  </span>
                </td>
                <td className="px-3 py-2 text-xs font-mono text-[var(--text-secondary)]">{item.layer}</td>
                <td className="px-3 py-2 text-xs text-[var(--text-primary)] max-w-md truncate">{item.message}</td>
                <td className="px-3 py-2 text-right text-xs font-mono text-[var(--text-secondary)]">{item.occurrences}</td>
                <td className="px-3 py-2 text-xs font-mono text-[var(--text-tertiary)] truncate">{item.affected_workflow ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function FrequencyPanel({
  data,
  loading,
}: {
  data: { total: number; buckets: { code: string; layer: string; count: number }[] } | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)] py-8">
        <RefreshCw className="h-4 w-4 animate-spin" />
        Computing frequency histogram…
      </div>
    );
  }

  if (!data || data.buckets.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-12 text-[var(--text-tertiary)]">
        <Layers className="h-8 w-8 opacity-40" />
        <span className="text-sm">No error frequency data available</span>
      </div>
    );
  }

  const maxCount = Math.max(...data.buckets.map((b) => b.count), 1);

  return (
    <div className="flex flex-col gap-3">
      <div className="text-xs text-[var(--text-tertiary)]">
        Total error instances: <span className="font-mono text-[var(--text-primary)]">{data.total}</span> · {data.buckets.length} signature(s)
      </div>
      <div className="flex flex-col gap-2">
        {data.buckets.map((bucket) => (
          <div key={`${bucket.code}-${bucket.layer}`} className="flex items-center gap-3">
            <span className="font-mono text-xs text-[var(--text-secondary)] w-48 truncate shrink-0" title={bucket.code}>
              {bucket.code} <span className="text-[var(--text-tertiary)]">@{bucket.layer}</span>
            </span>
            <div className="flex-1 h-5 bg-[var(--surface-raised)] rounded overflow-hidden">
              <div
                className="h-full bg-red-500/60 rounded"
                style={{ width: `${(bucket.count / maxCount) * 100}%` }}
              />
            </div>
            <span className="font-mono text-xs text-[var(--text-tertiary)] w-12 text-right">{bucket.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
