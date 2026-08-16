/**
 * Graph Evidence Panel - Stage 7 Graph Runtime Integration
 *
 * Slides in alongside the graph overlay to show evidence trails,
 * calculations, sources, and confidence for a selected node.
 *
 * Every graph node links back to source data via evidence trails.
 * Clicking an evidence link navigates to the source workspace.
 *
 * Architecture: ExplainabilityRuntime → Evidence visualization
 */

'use client';

import { useMemo } from 'react';
import { financialGraphRuntime } from '@/lib/graph';
import { cn } from '@/lib/utils';
import { FileText, Calculator, Link as LinkIcon, ShieldCheck, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

// ===== Props =====
interface GraphEvidencePanelProps {
  nodeId: string;
  onClose: () => void;
  onNavigate?: (deepLink: string) => void;
  className?: string;
}

// ===== Component =====
export function GraphEvidencePanel({ nodeId, onClose, onNavigate, className }: GraphEvidencePanelProps) {
  const payload = useMemo(() => {
    return financialGraphRuntime.explain(nodeId);
  }, [nodeId]);

  if (!payload) {
    return (
      <div className={cn('w-72 border-l border-[var(--border-default)] bg-[var(--surface-raised)] flex flex-col', className)}>
        <div className="px-3 py-2 border-b border-[var(--border-default)]">
          <span className="fin-caption text-[var(--text-tertiary)]">No evidence available</span>
        </div>
      </div>
    );
  }

  const confidencePct = payload.confidence;
  const confidenceLow = confidencePct < 80;

  return (
    <div className={cn('w-72 border-l border-[var(--border-default)] bg-[var(--surface-raised)] flex flex-col shrink-0', className)}>
      {/* Header */}
      <div className="px-3 py-2 border-b border-[var(--border-default)] flex items-center gap-2">
        <ShieldCheck className={cn('h-3.5 w-3.5', confidenceLow ? 'text-[var(--color-warning-500)]' : 'text-[var(--color-positive-500)]')} />
        <span className="fin-label font-medium text-[var(--text-primary)]">Evidence &amp; Provenance</span>
        <div className="flex-1" />
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={onClose} aria-label="Close evidence panel">
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
        {/* Confidence badge */}
        <div className={cn(
          'flex items-center gap-2 px-2 py-1.5 rounded border',
          confidenceLow
            ? 'bg-[var(--color-warning-50)] border-[var(--color-warning-200)] text-[var(--color-warning-700)]'
            : 'bg-[var(--color-positive-50)] border-[var(--color-positive-200)] text-[var(--color-positive-700)]',
        )}>
          <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
          <span className="fin-body-small font-medium">
            Confidence: {confidencePct}%
          </span>
          {confidenceLow && (
            <span className="fin-caption ml-auto italic">low confidence</span>
          )}
        </div>

        {/* Evidence items */}
        {payload.evidence.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-1.5">
              <FileText className="h-3 w-3 text-[var(--text-tertiary)]" />
              <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Evidence</span>
            </div>
            {payload.evidence.map((item, idx) => (
              <div
                key={idx}
                className={cn(
                  'px-2 py-1.5 rounded border text-left',
                  confidenceLow && item.confidence !== undefined && item.confidence < 80
                    ? 'border-dashed border-[var(--color-warning-300)] bg-[var(--color-warning-50)]'
                    : 'border-[var(--border-subtle)] bg-[var(--surface-default)]',
                )}
              >
                <p className="fin-body-small text-[var(--text-primary)]">{item.summary}</p>
                {item.confidence !== undefined && (
                  <p className="fin-caption text-[var(--text-tertiary)] mt-0.5">
                    Source: {item.source}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Calculation steps */}
        {payload.calculations.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-1.5">
              <Calculator className="h-3 w-3 text-[var(--text-tertiary)]" />
              <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Calculations</span>
            </div>
            {payload.calculations.map((calc, idx) => (
              <div key={idx} className="px-2 py-1.5 border border-[var(--border-subtle)] rounded bg-[var(--surface-default)]">
                <p className="fin-body-small font-medium text-[var(--text-primary)]">{calc.name}</p>
                <p className="fin-caption text-[var(--text-tertiary)] mt-0.5">{calc.description}</p>
              </div>
            ))}
          </div>
        )}

        {/* Sources */}
        {payload.sources.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-1.5">
              <LinkIcon className="h-3 w-3 text-[var(--text-tertiary)]" />
              <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Sources</span>
            </div>
            {payload.sources.map((source, idx) => (
              <button
                key={idx}
                onClick={() => onNavigate?.(`${source.id}`)}
                className="flex items-center gap-2 px-2 py-1.5 border border-[var(--border-subtle)] rounded bg-[var(--surface-default)] hover:bg-[var(--surface-interactive)] transition-colors text-left"
              >
                <LinkIcon className="h-3 w-3 text-[var(--text-tertiary)] shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="fin-body-small text-[var(--text-primary)] truncate">{source.label}</p>
                  <p className="fin-caption text-[var(--text-tertiary)]">{source.type}</p>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Trace path */}
        {payload.trace_path && payload.trace_path.path.length > 1 && (
          <div className="flex flex-col gap-1.5">
            <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Trace Path</span>
            <div className="flex flex-wrap gap-1">
              {payload.trace_path.path.map((pathId, idx) => (
                <div key={idx} className="flex items-center gap-1">
                  <span className="fin-caption font-mono text-[var(--text-secondary)] px-1.5 py-0.5 bg-[var(--surface-default)] border border-[var(--border-subtle)] rounded">
                    {pathId.slice(0, 8)}…
                  </span>
                  {idx < payload.trace_path!.path.length - 1 && (
                    <ArrowRight className="h-3 w-3 text-[var(--text-tertiary)]" />
                  )}
                </div>
              ))}
            </div>
            <p className="fin-caption text-[var(--text-tertiary)]">
              {payload.trace_path.steps} hops · {payload.trace_path.complete ? 'complete' : 'partial'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
