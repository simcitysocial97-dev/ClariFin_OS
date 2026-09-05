/**
 * Platform Change Intelligence Page — M9-C57 Phase 10
 *
 * Blast radius analysis: changed files → affected capabilities →
 * stale evidence → recommended verification → risk assessment.
 * Data source: /platform/v1/change/intelligence.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  GitBranch,
  ShieldAlert,
  TestTube,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChangedFile {
  path: string;
  change_type: string;
}

interface ChangeIntelligenceData {
  changed_files: ChangedFile[];
  affected_capabilities: string[];
  stale_evidence: string[];
  affected_tests: string[];
  affected_workflows: string[];
  recommended_verification: string[];
  risk: string;
  generated_from: string;
}

interface ChangeIntelligenceResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: ChangeIntelligenceData;
}

export default function ChangeIntelligencePage() {
  const router = useRouter();
  const [data, setData] = useState<ChangeIntelligenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/platform/v1/change/intelligence')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<ChangeIntelligenceResponse>;
      })
      .then((json) => setData(json.data))
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const riskColor =
    data?.risk === 'HIGH' ? 'text-red-400 bg-red-500/10 border-red-500/30' :
    data?.risk === 'MEDIUM' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' :
    'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';

  return (
    <div className="flex flex-col gap-4 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push('/platform/diagnostics')}
          className="text-xs text-[var(--text-tertiary)] underline hover:text-[var(--text-secondary)]"
        >
          ← Diagnostics
        </button>
        <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Zap className="h-5 w-5 text-blue-400" />
          Change Intelligence
        </h1>
      </div>

      {loading && (
        <div className="text-sm text-[var(--text-tertiary)] py-8">Computing blast radius…</div>
      )}

      {error && (
        <div className="text-sm text-red-400 py-8">Error: {error}</div>
      )}

      {data && (
        <>
          {/* Risk banner */}
          <div className={cn('rounded-lg border p-4 flex items-center gap-4', riskColor)}>
            {data.risk === 'HIGH' ? (
              <ShieldAlert className="h-8 w-8 shrink-0" />
            ) : data.risk === 'MEDIUM' ? (
              <AlertTriangle className="h-8 w-8 shrink-0" />
            ) : (
              <CheckCircle2 className="h-8 w-8 shrink-0" />
            )}
            <div className="flex-1">
              <div className="text-xl font-bold font-mono">{data.risk} RISK</div>
              <div className="text-sm opacity-80">
                {data.affected_capabilities.length} capability(s) affected ·
                {data.changed_files.length} file(s) changed ·
                last computed {data.generated_from.slice(11, 19)}
              </div>
            </div>
            <Link
              href="/platform/verification"
              className="text-xs px-3 py-2 rounded-lg bg-violet-500/20 text-violet-300 hover:bg-violet-500/30 transition-colors shrink-0"
            >
              Run Verification
            </Link>
          </div>

          {/* Changed files */}
          <Panel title="Changed Files" icon={<FileText className="h-4 w-4 text-blue-400" />}>
            {data.changed_files.length === 0 ? (
              <div className="text-sm text-[var(--text-tertiary)] italic">No repository changes detected</div>
            ) : (
              <div className="flex flex-col gap-1">
                {data.changed_files.map((f) => (
                  <div key={f.path} className="flex items-center gap-3 text-xs font-mono">
                    <span className={cn(
                      'px-1.5 py-0.5 rounded text-xs shrink-0',
                      f.change_type === 'added' ? 'bg-emerald-500/20 text-emerald-400' :
                      f.change_type === 'removed' ? 'bg-red-500/20 text-red-400' :
                      'bg-blue-500/20 text-blue-400',
                    )}>
                      {f.change_type}
                    </span>
                    <span className="text-[var(--text-primary)] truncate">{f.path}</span>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          {/* Affected capabilities */}
          <Panel title="Affected Capabilities" icon={<GitBranch className="h-4 w-4 text-violet-400" />}>
            {data.affected_capabilities.length === 0 ? (
              <div className="text-sm text-emerald-400">No capabilities affected</div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {data.affected_capabilities.map((cap) => (
                  <Link
                    key={cap}
                    href={`/platform/capabilities/${encodeURIComponent(cap)}`}
                    className="text-xs font-mono px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-violet-500/50 hover:bg-violet-500/10 transition-colors"
                  >
                    {cap}
                  </Link>
                ))}
              </div>
            )}
          </Panel>

          {/* Stale evidence */}
          <Panel title="Stale Evidence" icon={<TestTube className="h-4 w-4 text-amber-400" />}>
            {data.stale_evidence.length === 0 ? (
              <div className="text-sm text-emerald-400">No evidence invalidated</div>
            ) : (
              <div className="flex flex-col gap-1">
                {data.stale_evidence.slice(0, 5).map((eid) => (
                  <div key={eid} className="text-xs font-mono text-[var(--text-secondary)]">
                    {eid}
                  </div>
                ))}
                {data.stale_evidence.length > 5 && (
                  <div className="text-xs text-[var(--text-tertiary)]">+{data.stale_evidence.length - 5} more</div>
                )}
              </div>
            )}
          </Panel>

          {/* Recommended verification */}
          <Panel title="Recommended Verification" icon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}>
            {data.recommended_verification.length === 0 ? (
              <div className="text-sm text-[var(--text-tertiary)]">No specific verification recommended</div>
            ) : (
              <div className="flex flex-col gap-2">
                {data.recommended_verification.map((rec) => (
                  <Link
                    key={rec}
                    href={`/platform/verification/run/${encodeURIComponent(rec)}`}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg border border-[var(--border-subtle)] hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-colors"
                  >
                    <TestTube className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span className="text-sm font-mono text-[var(--text-primary)]">{rec}</span>
                  </Link>
                ))}
              </div>
            )}
          </Panel>

          {/* Footer */}
          <div className="text-xs text-[var(--text-tertiary)] border-t border-[var(--border-subtle)] pt-2">
            Deterministic blast-radius analysis · sourced from C50 change_surface + blast_radius · no LLM
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function Panel({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4 flex flex-col gap-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
        {icon}
        {title}
      </div>
      <div className="flex flex-col gap-1">
        {children}
      </div>
    </div>
  );
}
