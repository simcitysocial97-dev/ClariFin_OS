/**
 * Right Inspector - Stage 8B Workspace Integration & Surface Migration
 *
 * Resizable inspector panel (280-420px).
 * Contains: Context, Explainability, Evidence Summary, Confidence, Recommendations, Related Nodes, Actions.
 * Metadata-driven: Sections come from WorkspaceRegistry.
 * Everything comes from ExplainabilityRuntime, IntelligenceRuntime, SelectionRuntime.
 * No duplicated calculations.
 */

'use client';

import { useState, useMemo } from 'react';
import { useWorkspace } from '@/lib/workspace/workspace-context';
import { commandCenterRuntime } from '@/lib/command-center';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import { ContextPanel } from '@/components/command-center/context-panel';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import {
  ChevronLeft,
  ChevronRight,
  Lightbulb,
  Link as LinkIcon,
} from 'lucide-react';

// ===== Inspector Section Components =====
function EvidenceSection() {
  // Evidence is shown based on selection
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Evidence</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Evidence chain for selected item</p>
      </CardContent>
    </Card>
  );
}

function InsightsSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Insights</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Workspace insights</p>
      </CardContent>
    </Card>
  );
}

function PatternsSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Patterns</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Behavior patterns</p>
      </CardContent>
    </Card>
  );
}

function CompositionSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Composition</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Asset composition</p>
      </CardContent>
    </Card>
  );
}

function TrendSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Trend</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Net worth trend</p>
      </CardContent>
    </Card>
  );
}

function AmortizationSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Amortization</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Loan schedule</p>
      </CardContent>
    </Card>
  );
}

function SimulationSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Simulation</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Prepayment impact</p>
      </CardContent>
    </Card>
  );
}

function AllocationSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Allocation</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Portfolio allocation</p>
      </CardContent>
    </Card>
  );
}

function ProjectionsSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Projections</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Future projections</p>
      </CardContent>
    </Card>
  );
}

function ScenariosSection() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">Scenarios</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">Scenario comparison</p>
      </CardContent>
    </Card>
  );
}

// ===== Section Mapping =====
// Note: ContextPanel is rendered separately with its required props
const inspectorSections: Record<string, React.ComponentType<Record<string, unknown>>> = {
  // context: ContextPanel, // Rendered separately with required props
  evidence: EvidenceSection,
  insights: InsightsSection,
  patterns: PatternsSection,
  composition: CompositionSection,
  trend: TrendSection,
  amortization: AmortizationSection,
  simulation: SimulationSection,
  allocation: AllocationSection,
  projections: ProjectionsSection,
  scenarios: ScenariosSection,
  related: () => null, // Handled separately
};

// ===== Right Inspector Component =====
interface RightInspectorProps {
  className?: string;
}

export function RightInspector({ className }: RightInspectorProps) {
  const { state } = useWorkspace();
  const [width, setWidth] = useState(320);
  const [collapsed, setCollapsed] = useState(false);

  // Get current workspace registration from registry
  const workspaceRegistration = useMemo(() => {
    return workspaceRegistry.get(state.currentWorkspace);
  }, [state.currentWorkspace]);

  // Get selected node from graph selection
  const selectedNodeId = useMemo(() => {
    const selection = commandCenterRuntime.getSelection();
    return selection.node_ids.length > 0 ? selection.node_ids[0] : null;
  }, []);

  // Get related nodes
  const relatedNodes = useMemo(() => {
    if (!selectedNodeId) return null;
    return commandCenterRuntime.getRelated(selectedNodeId, 2);
  }, [selectedNodeId]);

  // Get intelligence insights
  const intelligence = useMemo(() => {
    if (!selectedNodeId) return null;
    return commandCenterRuntime.computeIntelligence();
  }, [selectedNodeId]);

  // Get inspector sections from registry
  const sections = workspaceRegistration?.inspectorSections ?? ['context'];

  if (collapsed) {
    return (
      <aside
        className={cn(
          'fixed right-0 top-44 bottom-88 z-20 w-10 border-l bg-background',
          className,
        )}
      >
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(false)}
          className="h-8 w-8 mt-2"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </aside>
    );
  }

  return (
    <aside
      className={cn(
        'fixed right-0 top-44 bottom-88 z-20 border-l bg-background transition-all duration-300',
        `w-[${width}px]`,
        className,
      )}
      style={{ width: `${width}px` }}
    >
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex h-10 items-center justify-between border-b px-3">
          <span className="text-sm font-medium">Inspector</span>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setCollapsed(true)}
              className="h-6 w-6"
            >
              <ChevronRight className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setWidth(w => Math.max(280, w - 20))}
              className="h-6 w-6"
            >
              <ChevronLeft className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setWidth(w => Math.min(420, w + 20))}
              className="h-6 w-6"
            >
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1">
          <div className="p-3 space-y-3">
            {/* Context Panel - uses runtime data */}
            {sections.includes('context') && (
              <ContextPanel
                nodeId={selectedNodeId}
                onNavigateToNode={(nodeId) => {
                  window.location.href = `/${state.currentWorkspace}?id=${nodeId}`;
                }}
              />
            )}

            {/* Dynamic Sections from Registry */}
            {sections.map((section) => {
              if (section === 'context') return null; // Already rendered above
              if (section === 'related') return null; // Handled separately

              const SectionComponent = inspectorSections[section];
              if (!SectionComponent) return null;

              return (
                <SectionComponent key={section} />
              );
            })}

            {/* Recommendations from Intelligence */}
            {intelligence?.recommendations && intelligence.recommendations.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium flex items-center gap-1">
                    <Lightbulb className="h-3 w-3" />
                    Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <ul className="space-y-1">
                    {intelligence.recommendations.slice(0, 3).map((rec, idx) => (
                      <li key={idx} className="text-xs">
                        <span className="text-muted-foreground">{rec.reason}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Related Nodes (if workspace supports it) */}
            {sections.includes('related') && relatedNodes && relatedNodes.nodes.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium flex items-center gap-1">
                    <LinkIcon className="h-3 w-3" />
                    Related Nodes
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <ul className="space-y-1">
                    {relatedNodes.nodes.slice(0, 5).map(node => (
                      <li key={node.id}>
                        <button
                          onClick={() => {
                            window.location.href = node.deep_link ?? `/${node.workspace}`;
                          }}
                          className="text-xs text-blue-600 hover:underline text-left truncate w-full"
                        >
                          {node.label}
                        </button>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        </ScrollArea>
      </div>
    </aside>
  );
}