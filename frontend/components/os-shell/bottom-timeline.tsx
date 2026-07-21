/**
 * Bottom Timeline - Stage 8E Financial Operating System Shell
 *
 * Operating timeline panel (88px height).
 * Supports modes: Events, Forecast, Behaviour, Automation.
 * Uses Surface, CompactToolbar, FinancialIcon, FinancialBadge.
 */

'use client';

import { useState, useMemo } from 'react';
import { useWorkspace } from '@/lib/workspace/workspace-context';
import { commandCenterRuntime } from '@/lib/command-center';
import { Timeline } from '@/components/command-center/timeline';
import { CompactToolbar, ToolbarButton } from '@/components/primitives/toolbar-primitive/compact-toolbar';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { FinancialBadge } from '@/components/primitives/badge-semantic/financial-badge';
import { cn } from '@/lib/utils';
import { ChevronUp, ChevronDown } from 'lucide-react';

// ===== Timeline Mode =====
type TimelineMode = 'events' | 'forecast' | 'behaviour' | 'automation';

// ===== Bottom Timeline Component =====
interface BottomTimelineProps {
  className?: string;
}

export function BottomTimeline({ className }: BottomTimelineProps) {
  const { state } = useWorkspace();
  const [mode, setMode] = useState<TimelineMode>('events');
  const [collapsed, setCollapsed] = useState(false);

  // Get selection context
  const selection = useMemo(() => {
    return commandCenterRuntime.getSelection();
  }, [state.currentWorkspace]);

  if (collapsed) {
    return (
      <footer
        className={cn(
          'fixed bottom-0 left-[180px] right-0 z-20 h-8',
          'border-t border-[var(--border-default)]',
          'bg-[var(--surface-timeline)]',
          className,
        )}
      >
        <button
          onClick={() => setCollapsed(false)}
          className="flex items-center justify-start h-8 px-3 gap-1.5 w-full text-[var(--text-tertiary)] hover:bg-[var(--surface-interactive)]"
        >
          <ChevronUp className="h-3 w-3" />
          <span className="fin-caption">Timeline</span>
          {selection.node_ids.length > 0 && (
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-selection)]" />
          )}
        </button>
      </footer>
    );
  }

  return (
    <footer
      className={cn(
        'fixed bottom-0 left-[180px] right-0 z-20',
        'border-t border-[var(--border-default)]',
        'bg-[var(--surface-timeline)]',
        'h-20',
        className,
      )}
    >
      {/* Mode Tabs */}
      <div className="flex h-8 items-center gap-1 px-3 border-b border-[var(--border-default)]">
        <CompactToolbar size="sm">
          <ToolbarButton
            icon={() => <FinancialIcon name="history" size={13} />}
            label="Events"
            active={mode === 'events'}
            onClick={() => setMode('events')}
          />
          <ToolbarButton
            icon={() => <FinancialIcon name="forecast" size={13} />}
            label="Forecast"
            active={mode === 'forecast'}
            onClick={() => setMode('forecast')}
          />
          <ToolbarButton
            icon={() => <FinancialIcon name="behaviour" size={13} />}
            label="Behaviour"
            active={mode === 'behaviour'}
            onClick={() => setMode('behaviour')}
          />
          <ToolbarButton
            icon={() => <FinancialIcon name="automate" size={13} />}
            label="Automation"
            active={mode === 'automation'}
            onClick={() => setMode('automation')}
          />
        </CompactToolbar>

        <div className="ml-auto flex items-center gap-1.5">
          {selection.node_ids.length > 0 && (
            <FinancialBadge semantic="info" variant="outline" className="text-[9px] px-1">
              {selection.node_ids.length}
            </FinancialBadge>
          )}
          <button
            onClick={() => setCollapsed(true)}
            className="flex items-center justify-center h-5 w-5 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
            aria-label="Collapse timeline"
          >
            <ChevronDown className="h-2.5 w-2.5" />
          </button>
        </div>
      </div>

      {/* Timeline Content */}
      <div className="h-12 overflow-hidden">
        <Timeline
          onNodeSelect={(node) => {
            window.location.href = node.deep_link ?? `/${node.workspace}`;
          }}
        />
      </div>
    </footer>
  );
}