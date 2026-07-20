/**
 * Bottom Timeline - Stage 8A Financial Operating System Shell
 *
 * Persistent timeline panel (88px height).
 * Uses Timeline Runtime.
 * Supports: History, Forecast, Simulation, Audit.
 * Chronological navigation.
 */

'use client';

import { useState } from 'react';
import { Timeline } from '@/components/command-center/timeline';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  History,
  BarChart3,
  GitCompare,
  FileText,
  ChevronUp,
  ChevronDown,
} from 'lucide-react';

// ===== Timeline Mode =====
type TimelineMode = 'history' | 'forecast' | 'simulation' | 'audit';

// ===== Bottom Timeline Component =====
interface BottomTimelineProps {
  className?: string;
}

export function BottomTimeline({ className }: BottomTimelineProps) {
  const [mode, setMode] = useState<TimelineMode>('history');
  const [collapsed, setCollapsed] = useState(false);

  if (collapsed) {
    return (
      <footer
        className={cn(
          'fixed bottom-0 left-180 right-0 z-20 h-8 border-t bg-background',
          className,
        )}
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(false)}
          className="h-8 w-full justify-start px-3"
        >
          <ChevronUp className="h-3 w-3 mr-1" />
          <span className="text-xs">Timeline</span>
        </Button>
      </footer>
    );
  }

  return (
    <footer
      className={cn(
        'fixed bottom-0 left-180 right-0 z-20 border-t bg-background',
        'h-88', // 88px height
        className,
      )}
    >
      <div className="flex h-8 items-center gap-1 border-b px-3">
        {/* Mode Tabs */}
        <div className="flex items-center gap-1">
          <Button
            variant={mode === 'history' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setMode('history')}
            className="h-6 px-2 text-xs"
          >
            <History className="h-3 w-3 mr-1" />
            History
          </Button>
          <Button
            variant={mode === 'forecast' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setMode('forecast')}
            className="h-6 px-2 text-xs"
          >
            <BarChart3 className="h-3 w-3 mr-1" />
            Forecast
          </Button>
          <Button
            variant={mode === 'simulation' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setMode('simulation')}
            className="h-6 px-2 text-xs"
          >
            <GitCompare className="h-3 w-3 mr-1" />
            Simulation
          </Button>
          <Button
            variant={mode === 'audit' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setMode('audit')}
            className="h-6 px-2 text-xs"
          >
            <FileText className="h-3 w-3 mr-1" />
            Audit
          </Button>
        </div>

        {/* Collapse Button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(true)}
          className="h-6 w-6 ml-auto"
        >
          <ChevronDown className="h-3 w-3" />
        </Button>
      </div>

      {/* Timeline Content */}
      <div className="h-80 overflow-hidden">
        <Timeline
          onNodeSelect={(node) => {
            window.location.href = node.deep_link ?? `/${node.workspace}`;
          }}
        />
      </div>
    </footer>
  );
}