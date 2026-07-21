/**
 * Right Inspector - Stage 8E Financial Operating System Shell
 *
 * Contextual intelligence workspace.
 * Resizable (280-420px).
 * Contains reusable InspectorBlocks driven by WorkspaceRegistry.
 * Uses Panel, Surface, ScrollRegion, FinancialIcon, FinancialBadge.
 */

'use client';

import { useState, useMemo } from 'react';
import { useWorkspace } from '@/lib/workspace/workspace-context';
import { commandCenterRuntime } from '@/lib/command-center';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import { ContextPanel } from '@/components/command-center/context-panel';
import { EvidenceTree } from '@/components/visualization/evidence-tree/evidence-tree';
import { Surface } from '@/components/primitives/surface/surface';
import { ScrollRegion } from '@/components/primitives/layout/scroll-region';
import { Stack } from '@/components/primitives/layout/stack';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { FinancialBadge } from '@/components/primitives/badge-semantic/financial-badge';
import { cn } from '@/lib/utils';
import { ChevronLeft, ChevronRight, Lightbulb, Link as LinkIcon, Minimize2, Maximize2 } from 'lucide-react';

// ===== Inspector Block =====
interface InspectorBlockProps {
  title: string;
  icon?: string;
  children: React.ReactNode;
}

function InspectorBlock({ title, icon, children }: InspectorBlockProps) {
  return (
    <Surface variant="raised" density="compact" className="border-0 border-b border-[var(--border-subtle)] last:border-b-0">
      <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-[var(--border-subtle)]">
        {icon && <FinancialIcon name={icon} size={12} className="text-[var(--text-tertiary)]" />}
        <span className="fin-caption font-medium uppercase tracking-wider">{title}</span>
      </div>
      <div className="px-3 py-2">
        {children}
      </div>
    </Surface>
  );
}

// ===== Section Components =====
function InsightsSection() {
  return (
    <InspectorBlock title="Insights" icon="behaviour">
      <p className="fin-body-small">Select an entity to view insights</p>
    </InspectorBlock>
  );
}

function PatternsSection() {
  return (
    <InspectorBlock title="Patterns" icon="behaviour">
      <p className="fin-body-small">Financial behavior patterns</p>
    </InspectorBlock>
  );
}

function CompositionSection() {
  return (
    <InspectorBlock title="Composition" icon="pie-chart">
      <p className="fin-body-small">Asset composition</p>
    </InspectorBlock>
  );
}

function TrendSection() {
  return (
    <InspectorBlock title="Trend" icon="trending-up">
      <p className="fin-body-small">Net worth trend</p>
    </InspectorBlock>
  );
}

function AmortizationSection() {
  return (
    <InspectorBlock title="Amortization" icon="loan">
      <p className="fin-body-small">Loan amortization schedule</p>
    </InspectorBlock>
  );
}

function SimulationSection() {
  return (
    <InspectorBlock title="Simulation" icon="simulate">
      <p className="fin-body-small">What-if analysis</p>
    </InspectorBlock>
  );
}

function AllocationSection() {
  return (
    <InspectorBlock title="Allocation" icon="investment">
      <p className="fin-body-small">Portfolio allocation</p>
    </InspectorBlock>
  );
}

function ProjectionsSection() {
  return (
    <InspectorBlock title="Projections" icon="forecast">
      <p className="fin-body-small">Future projections</p>
    </InspectorBlock>
  );
}

function ScenariosSection() {
  return (
    <InspectorBlock title="Scenarios" icon="crystal-ball">
      <p className="fin-body-small">Scenario comparison</p>
    </InspectorBlock>
  );
}

function ActionsSection() {
  return (
    <InspectorBlock title="Actions" icon="automate">
      <p className="fin-body-small">Suggested actions</p>
    </InspectorBlock>
  );
}

// ===== Section Mapping =====
const inspectorSections: Record<string, React.ComponentType> = {
  insights: InsightsSection,
  patterns: PatternsSection,
  composition: CompositionSection,
  trend: TrendSection,
  amortization: AmortizationSection,
  simulation: SimulationSection,
  allocation: AllocationSection,
  projections: ProjectionsSection,
  scenarios: ScenariosSection,
  actions: ActionsSection,
};

// ===== Right Inspector Component =====
interface RightInspectorProps {
  className?: string;
}

export function RightInspector({ className }: RightInspectorProps) {
  const { state } = useWorkspace();
  const [width, setWidth] = useState(320);
  const [collapsed, setCollapsed] = useState(false);

  // Get workspace registration
  const workspaceRegistration = useMemo(() => {
    return workspaceRegistry.get(state.currentWorkspace);
  }, [state.currentWorkspace]);

  // Get selection
  const selectedNodeId = useMemo(() => {
    const selection = commandCenterRuntime.getSelection();
    return selection.node_ids.length > 0 ? selection.node_ids[0] : null;
  }, [state.currentWorkspace]);

  // Get related nodes
  const relatedNodes = useMemo(() => {
    if (!selectedNodeId) return null;
    return commandCenterRuntime.getRelated(selectedNodeId, 2);
  }, [selectedNodeId]);

  // Get intelligence
  const intelligence = useMemo(() => {
    if (!selectedNodeId) return null;
    return commandCenterRuntime.computeIntelligence();
  }, [selectedNodeId]);

  // Get sections
  const sections = workspaceRegistration?.inspectorSections ?? ['context'];

  if (collapsed) {
    return (
      <aside
        className={cn(
          'fixed right-0 top-11 bottom-[108px] z-20',
          'w-10 border-l border-[var(--border-default)]',
          'bg-[var(--surface-default)]',
          'flex flex-col items-center pt-2 gap-1',
          className,
        )}
      >
        <button
          onClick={() => setCollapsed(false)}
          className="flex items-center justify-center h-7 w-7 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
          aria-label="Expand inspector"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
        </button>
        {selectedNodeId && (
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-selection)]" />
        )}
      </aside>
    );
  }

  return (
    <aside
      className={cn(
        'fixed right-0 top-11 bottom-[108px] z-20',
        'border-l border-[var(--border-default)]',
        'bg-[var(--surface-default)]',
        'flex flex-col',
        className,
      )}
      style={{ width: `${width}px` }}
    >
      {/* Header */}
      <div className="flex items-center justify-between h-10 px-3 border-b border-[var(--border-default)] shrink-0">
        <div className="flex items-center gap-1.5">
          <FinancialIcon name="search" size={13} className="text-[var(--text-tertiary)]" />
          <span className="fin-label font-medium text-[var(--text-primary)]">Inspector</span>
        </div>
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => setWidth(w => Math.max(280, w - 20))}
            className="flex items-center justify-center h-6 w-5 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
            aria-label="Decrease width"
          >
            <Minimize2 className="h-2.5 w-2.5" />
          </button>
          <button
            onClick={() => setWidth(w => Math.min(420, w + 20))}
            className="flex items-center justify-center h-6 w-5 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
            aria-label="Increase width"
          >
            <Maximize2 className="h-2.5 w-2.5" />
          </button>
          <button
            onClick={() => setCollapsed(true)}
            className="flex items-center justify-center h-6 w-6 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
            aria-label="Collapse inspector"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Content */}
      <ScrollRegion className="flex-1">
        <div className="divide-y divide-[var(--border-subtle)]">
          {/* Context Panel */}
          {sections.includes('context') && (
            <Surface variant="raised" density="compact" className="border-0 border-b border-[var(--border-subtle)] last:border-b-0">
              <ContextPanel
                nodeId={selectedNodeId}
                onNavigateToNode={(nodeId) => {
                  window.location.href = `/${state.currentWorkspace}?id=${nodeId}`;
                }}
              />
            </Surface>
          )}

          {/* Evidence Tree */}
          {sections.includes('evidence') && (
            <Surface variant="raised" density="compact" className="border-0 border-b border-[var(--border-subtle)] last:border-b-0">
              <EvidenceTree nodeId={selectedNodeId} />
            </Surface>
          )}

          {/* Dynamic Sections */}
          {sections.map((section) => {
            if (section === 'context' || section === 'evidence' || section === 'related') return null;
            const SectionComponent = inspectorSections[section];
            if (!SectionComponent) return null;
            return <SectionComponent key={section} />;
          })}

          {/* Recommendations */}
          {intelligence?.recommendations && intelligence.recommendations.length > 0 && (
            <InspectorBlock title="Recommendations" icon="behaviour">
              <Stack gap={1}>
                {intelligence.recommendations.slice(0, 4).map((rec, idx) => (
                  <div key={idx} className="flex items-start gap-1.5">
                    <Lightbulb className="h-3 w-3 mt-0.5 text-[var(--color-warning-500)] shrink-0" />
                    <span className="fin-body-small text-[var(--text-secondary)]">{rec.reason}</span>
                  </div>
                ))}
              </Stack>
            </InspectorBlock>
          )}

          {/* Related Nodes */}
          {sections.includes('related') && relatedNodes && relatedNodes.nodes.length > 0 && (
            <InspectorBlock title="Related" icon="transaction">
              <Stack gap={1}>
                {relatedNodes.nodes.slice(0, 5).map(node => (
                  <button
                    key={node.id}
                    onClick={() => {
                      window.location.href = node.deep_link ?? `/${node.workspace}`;
                    }}
                    className="flex items-center gap-1.5 fin-body-small text-[var(--text-link)] hover:underline text-left w-full"
                  >
                    <LinkIcon className="h-2.5 w-2.5 shrink-0" />
                    <span className="truncate">{node.label}</span>
                  </button>
                ))}
              </Stack>
            </InspectorBlock>
          )}
        </div>
      </ScrollRegion>

      {/* Footer */}
      <div className="h-7 px-3 border-t border-[var(--border-default)] flex items-center shrink-0">
        <div className="flex items-center gap-1.5">
          <span className="fin-caption">
            {selectedNodeId ? `Node: ${selectedNodeId.slice(0, 8)}` : 'No selection'}
          </span>
          {selectedNodeId && (
            <FinancialBadge semantic="info" variant="outline" className="text-[9px] px-1">
              Active
            </FinancialBadge>
          )}
        </div>
      </div>
    </aside>
  );
}