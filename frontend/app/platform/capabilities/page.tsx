/**
 * Platform Capabilities Page — M9-C57 Phase 9C
 *
 * Capability Explorer: tree/list view of all C50 capabilities with
 * filtering by stage, search, and click-through to detail.
 * Data source: /platform/v1/capabilities.
 */

'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useCapabilityList } from '@/lib/hooks/use-platform-capabilities';
import { Layers, Search, Filter, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function CapabilitiesPage() {
  const { data, isLoading } = useCapabilityList();
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState<string>('all');

  const categories = data?.data?.categories ?? [];
  const items = useMemo(() => data?.data?.items ?? [], [data?.data?.items]);

  const filtered = useMemo(() => {
    let result = items;
    if (stageFilter !== 'all') {
      result = result.filter((c) => c.stage === stageFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (c) =>
          c.id.toLowerCase().includes(q) ||
          c.name.toLowerCase().includes(q) ||
          c.stage.toLowerCase().includes(q),
      );
    }
    return result;
  }, [items, stageFilter, search]);

  return (
    <div className="flex flex-col gap-4 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Layers className="h-5 w-5 text-blue-400" />
            Capability Explorer
          </h1>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
            {data?.data?.count ?? 0} capabilities · {categories.length} stages · sourced from C50 catalog
          </p>
        </div>
        <div className="text-xs text-[var(--text-tertiary)] font-mono">
          {categories.join(' · ')}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-tertiary)]" />
          <input
            type="text"
            placeholder="Search capabilities…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--border-default)]"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-[var(--text-tertiary)]" />
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="text-sm rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] text-[var(--text-primary)] px-3 py-1.5 focus:outline-none focus:border-[var(--border-default)]"
          >
            <option value="all">All stages</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
        <span className="text-xs text-[var(--text-tertiary)] font-mono">
          {filtered.length} of {items.length}
        </span>
      </div>

      {/* Grid */}
      {isLoading ? (
        <LoadingState />
      ) : filtered.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((cap) => (
            <CapabilityCard key={cap.id} cap={cap} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function CapabilityCard({
  cap,
}: {
  cap: { id: string; name: string; stage: string; cost: string; authorization: string; produces: string[]; triggers: string[] };
}) {
  return (
    <Link
      href={`/platform/capabilities/${encodeURIComponent(cap.id)}`}
      className="block rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4 hover:border-[var(--border-default)] hover:bg-[var(--surface-raised)] transition-colors"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-[var(--text-primary)] truncate">{cap.id}</div>
          <div className="text-xs text-[var(--text-tertiary)] truncate">{cap.name}</div>
        </div>
        <span className={cn(
          'shrink-0 text-xs px-2 py-0.5 rounded-full font-mono',
          cap.cost === 'P0' ? 'bg-emerald-500/20 text-emerald-400' :
          cap.cost === 'P1' ? 'bg-amber-500/20 text-amber-400' :
          cap.cost === 'P2' ? 'bg-blue-500/20 text-blue-400' :
          'bg-[var(--surface-raised)] text-[var(--text-tertiary)]',
        )}>
          {cap.cost}
        </span>
      </div>
      <div className="flex flex-wrap gap-1 mt-2">
        <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--surface-raised)] text-[var(--text-tertiary)] font-mono">
          {cap.stage}
        </span>
        <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--surface-raised)] text-[var(--text-tertiary)] font-mono">
          {cap.authorization}
        </span>
      </div>
      {cap.produces.length > 0 && (
        <div className="mt-2 text-xs text-[var(--text-tertiary)] font-mono truncate" title={cap.produces.join(', ')}>
          → {cap.produces.slice(0, 2).join(', ')}{cap.produces.length > 2 ? ` +${cap.produces.length - 2}` : ''}
        </div>
      )}
    </Link>
  );
}

function LoadingState() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4 animate-pulse">
          <div className="h-4 bg-[var(--surface-raised)] rounded w-3/4 mb-2" />
          <div className="h-3 bg-[var(--surface-raised)] rounded w-1/2 mb-3" />
          <div className="flex gap-1">
            <div className="h-5 bg-[var(--surface-raised)] rounded w-12" />
            <div className="h-5 bg-[var(--surface-raised)] rounded w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-2 py-16 text-[var(--text-tertiary)]">
      <Zap className="h-8 w-8 opacity-40" />
      <span className="text-sm">No capabilities match your filters</span>
      <span className="text-xs">Try adjusting search or stage filter</span>
    </div>
  );
}
