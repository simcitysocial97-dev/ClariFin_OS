/**
 * Decision Feed Item - Stage 8E-B Command Center
 *
 * Individual investigation item in the Decision Feed.
 * Every item answers: Why should I care? What changed? Evidence? Confidence? Impact? Next Action?
 */

'use client';

import { Surface } from '@/components/primitives/surface/surface';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { FinancialBadge } from '@/components/primitives/badge-semantic/financial-badge';
import { ConfidenceBadge } from '@/components/primitives/confidence-badge/confidence-badge';
import { MoneyValue } from '@/components/primitives/data-display/money-value';
import { TimestampValue } from '@/components/primitives/data-display/timestamp-value';
import { Stack } from '@/components/primitives/layout/stack';
import type { GraphNode } from '@/lib/graph';
import { cn } from '@/lib/utils';

// ===== Feed Item Types =====
export type FeedItemType =
  | 'high-priority'
  | 'cashflow-risk'
  | 'upcoming-payments'
  | 'investment-drift'
  | 'forecast-alert'
  | 'behaviour-change'
  | 'automation-failure'
  | 'recommendation';

// ===== Feed Item Data =====
export interface FeedItemData {
  id: string;
  type: FeedItemType;
  title: string;
  description: string;
  nodeId?: string;
  valuePaise?: number;
  confidence: number;
  evidenceCount: number;
  impactPaise?: number;
  nextAction?: string;
  timestamp?: string;
  node?: GraphNode;
}

// ===== Props =====
interface DecisionFeedItemProps {
  item: FeedItemData;
  onSelect?: (nodeId: string) => void;
  className?: string;
}

// ===== Type Config =====
const TYPE_CONFIG: Record<FeedItemType, { label: string; icon: string; semantic: 'positive' | 'negative' | 'warning' | 'info' }> = {
  'high-priority': { label: 'High Priority', icon: 'alert', semantic: 'warning' },
  'cashflow-risk': { label: 'Cashflow Risk', icon: 'cashflow', semantic: 'negative' },
  'upcoming-payments': { label: 'Upcoming', icon: 'calendar', semantic: 'info' },
  'investment-drift': { label: 'Drift', icon: 'investment', semantic: 'warning' },
  'forecast-alert': { label: 'Forecast', icon: 'forecast', semantic: 'info' },
  'behaviour-change': { label: 'Change', icon: 'behaviour', semantic: 'info' },
  'automation-failure': { label: 'Failed', icon: 'automate', semantic: 'negative' },
  'recommendation': { label: 'Action', icon: 'behaviour', semantic: 'positive' },
};

// ===== Decision Feed Item Component =====
export function DecisionFeedItem({
  item,
  onSelect,
  className,
}: DecisionFeedItemProps) {
  const config = TYPE_CONFIG[item.type];

  // Handle click - focus graph and open inspector
  const handleClick = () => {
    if (item.nodeId) {
      onSelect?.(item.nodeId);
    }
  };

  return (
    <Surface
      variant="interactive"
      density="compact"
      className={cn(
        'cursor-pointer transition-all duration-150',
        'hover:bg-[var(--surface-interactive)]',
        'border-0 border-b border-[var(--border-subtle)] last:border-b-0',
        className
      )}
      onClick={handleClick}
    >
      <div className="px-3 py-2">
        <Stack gap={1}>
          {/* Header: Icon, Title, Badge */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 min-w-0">
              <FinancialIcon name={config.icon} size={12} className="text-[var(--text-tertiary)] shrink-0" />
              <span className="fin-label font-medium truncate">{item.title}</span>
            </div>
            <FinancialBadge semantic={config.semantic} variant="outline" className="text-[9px] px-1 shrink-0">
              {config.label}
            </FinancialBadge>
          </div>

          {/* Description */}
          <p className="fin-body-small text-[var(--text-secondary)] line-clamp-2">
            {item.description}
          </p>

          {/* Meta Row */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ConfidenceBadge confidence={item.confidence} showLabel={false} />
              <span className="fin-caption">
                {item.evidenceCount} evidence
              </span>
            </div>

            {item.valuePaise !== undefined && (
              <MoneyValue paise={item.valuePaise} variant="compact" />
            )}
          </div>

          {/* Next Action */}
          {item.nextAction && (
            <div className="flex items-center gap-1.5 pt-1 border-t border-[var(--border-subtle)]">
              <FinancialIcon name="automate" size={10} className="text-[var(--color-info-500)]" />
              <span className="fin-caption text-[var(--text-link)]">
                {item.nextAction}
              </span>
            </div>
          )}

          {/* Timestamp */}
          {item.timestamp && (
            <TimestampValue
              value={item.timestamp}
              format="relative"
              className="fin-timestamp text-[var(--text-tertiary)]"
            />
          )}
        </Stack>
      </div>
    </Surface>
  );
}
