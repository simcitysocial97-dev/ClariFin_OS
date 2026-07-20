/**
 * Timeline - Stage 5 Command Center Platform
 *
 * Chronological financial activity view.
 * Graph-backed timeline showing salary, transfers, expenses, investments, loan payments, forecasts.
 * All navigation flows through graph nodes.
 */

'use client';

import { useMemo } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import type { GraphNode } from '@/lib/graph';
import { formatINR } from '@/lib/utils/format';
import { Card, CardContent } from '@/components/ui/card';

// ===== Timeline Event =====
interface TimelineEvent {
  id: string;
  date: string;
  label: string;
  value_paise?: number;
  type: string;
  workspace: string;
}

// ===== Props =====
interface TimelineProps {
  onNodeSelect?: (node: GraphNode) => void;
  className?: string;
}

// ===== Component =====
export function Timeline({
  onNodeSelect,
  className = '',
}: TimelineProps) {
  // Get current graph
  const graph = commandCenterRuntime.getCurrentGraph();

  // Build timeline events from graph nodes
  const events = useMemo((): TimelineEvent[] => {
    if (!graph) return [];

    const events: TimelineEvent[] = [];

    for (const node of graph.nodes) {
      if (node.date) {
        events.push({
          id: node.id,
          date: node.date,
          label: node.label,
          value_paise: node.value_paise,
          type: node.type,
          workspace: node.workspace,
        });
      }
    }

    // Sort by date
    return events.sort((a, b) => a.date.localeCompare(b.date));
  }, [graph]);

  // Group events by month
  const eventsByMonth = useMemo(() => {
    const groups: Record<string, TimelineEvent[]> = {};
    for (const event of events) {
      const month = event.date.substring(0, 7); // YYYY-MM
      if (!groups[month]) groups[month] = [];
      groups[month].push(event);
    }
    return groups;
  }, [events]);

  if (events.length === 0) {
    return (
      <div className={`p-4 ${className}`}>
        <p className="text-gray-500 text-sm">No timeline events available</p>
      </div>
    );
  }

  return (
    <div className={`p-2 overflow-y-auto ${className}`}>
      {Object.entries(eventsByMonth).map(([month, monthEvents]) => (
        <div key={month} className="mb-4">
          <h3 className="text-xs font-medium text-gray-500 mb-2 px-2">
            {new Date(month).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
            })}
          </h3>
          <div className="space-y-1">
            {monthEvents.map(event => (
              <Card
                key={event.id}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => {
                  const node = graph?.nodes.find(n => n.id === event.id);
                  if (node) onNodeSelect?.(node);
                }}
              >
                <CardContent className="p-2 py-1">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{event.label}</p>
                      <p className="text-xs text-gray-500">{event.type}</p>
                    </div>
                    {event.value_paise !== undefined && (
                      <span className="text-sm text-gray-700">
                        {formatINR(event.value_paise)}
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}