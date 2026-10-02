/**
 * Metrics Strip - Stage 8E-B Command Center
 *
 * Compact horizontal strip of financial metrics.
 * Each metric is an entry point into investigation.
 *
 * Architecture: MetricsStrip → MetricTile → Graph Navigation
 */

'use client';

import { useMemo, useCallback } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import type { GraphResult } from '@/lib/graph';
import { MetricTile } from '@/components/primitives/metric-tile/metric-tile';
import { ConfidenceBadge } from '@/components/primitives/confidence-badge/confidence-badge';
import { Surface } from '@/components/primitives/surface/surface';
import { cn } from '@/lib/utils';

// ===== Metric Types =====
export type MetricType =
  | 'net-worth'
  | 'liquidity'
  | 'monthly-cashflow'
  | 'investment-return'
  | 'debt-ratio'
  | 'forecast-confidence'
  | 'automation-success';

/**
 * How a metric's value must be presented.
 *
 * M10-A3: `investment-return`, `debt-ratio`, `forecast-confidence` and
 * `automation-success` are dimensionless ratios. They were declared as
 * `valuePaise` and rendered through `MoneyValue`, after being scaled by 10000
 * to look like a paise amount — so a 42% debt ratio was displayed to the user
 * as "₹4,20,000.00". Money formatting is not permitted on a ratio; the unit is
 * now declared per metric and drives the renderer.
 */
export type MetricFormat = 'money' | 'percent' | 'number';

// ===== Metric Data =====
export interface MetricData {
  id: MetricType;
  label: string;
  /**
   * For `format: 'money'` this is a paise amount. For `percent` / `number` it
   * is the already-scaled magnitude in that unit.
   */
  value: number;
  format: MetricFormat;
  /** Decimal places for the non-money formats. */
  precision?: number;
  /**
   * Period-over-period change in PAISE. Present only when the graph actually
   * carries a comparison period — the strip never invents one.
   */
  deltaPaise?: number;
  deltaPercent?: number;
  /**
   * Real confidence (0-100) from the graph nodes that produced the value.
   * Absent when the metric aggregates nodes that carry no confidence of their
   * own, in which case no confidence badge is shown.
   */
  confidence?: number;
  nodeId?: string;
}

// ===== Helpers =====

type GraphNodeLike = GraphResult['nodes'][number];

/** Coerce an unknown metadata/confidence value to a finite number, else 0. */
function num(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

const MONTH_FORMATTER = new Intl.DateTimeFormat('en-IN', { month: 'short', year: 'numeric', timeZone: 'UTC' });

/**
 * Net cashflow of the most recent calendar month present in the graph.
 *
 * A metric labelled "Monthly Cashflow" must actually be one month. The label
 * carries the month it covers so the number is self-describing, and the mean
 * confidence of the contributing nodes is reported instead of a literal.
 */
function bucketLatestMonth(transactions: GraphNodeLike[]): {
  label: string;
  netPaise: number;
  confidence?: number;
  nodeId?: string;
} {
  const byMonth = new Map<string, GraphNodeLike[]>();

  for (const node of transactions) {
    if (!node.date) continue;
    const parsed = new Date(node.date);
    if (Number.isNaN(parsed.getTime())) continue;
    const key = `${parsed.getUTCFullYear()}-${String(parsed.getUTCMonth() + 1).padStart(2, '0')}`;
    const bucket = byMonth.get(key);
    if (bucket) bucket.push(node);
    else byMonth.set(key, [node]);
  }

  if (byMonth.size === 0) {
    return {
      label: 'Monthly Cashflow (no dated transactions)',
      netPaise: 0,
    };
  }

  const latestKey = [...byMonth.keys()].sort().at(-1)!;
  const bucket = byMonth.get(latestKey)!;
  const netPaise = bucket.reduce((sum, n) => sum + (n.value_paise ?? 0), 0);
  const [year, month] = latestKey.split('-').map(Number);
  const label = `Monthly Cashflow · ${MONTH_FORMATTER.format(new Date(Date.UTC(year, month - 1, 1)))}`;

  // Only report a confidence when the contributing nodes actually carry one.
  const confidences = bucket
    .map(n => n.confidence)
    .filter((c): c is number => typeof c === 'number' && Number.isFinite(c));

  return {
    label,
    netPaise,
    confidence: confidences.length > 0 ? Math.round(mean(confidences)) : undefined,
    nodeId: bucket[0]?.id,
  };
}

// ===== Props =====
interface MetricsStripProps {
  onMetricSelect?: (nodeId: string) => void;
  className?: string;
}

// ===== Metrics Strip Component =====
export function MetricsStrip({
  onMetricSelect,
  className,
}: MetricsStripProps) {
  // Get current graph
  const graph = commandCenterRuntime.getCurrentGraph();

  // Calculate metrics from graph
  const metrics = useMemo((): MetricData[] => {
    if (!graph) return [];

    // Find relevant nodes
    const accounts = graph.nodes.filter(n => n.type === 'account');
    const transactions = graph.nodes.filter(n => n.type === 'transaction');
    const loans = graph.nodes.filter(n => n.type === 'loan');
    const investments = graph.nodes.filter(n => n.type === 'investment');
    const holdings = graph.nodes.filter(n => n.type === 'holding');
    const forecasts = graph.nodes.filter(n => n.type === 'forecast_projection');

    // Net Worth: Sum of all account balances
    const netWorth = accounts.reduce((sum, n) => sum + (n.value_paise ?? 0), 0);

    // Liquidity: Sum of current account balances (positive)
    const liquidity = accounts
      .filter(n => (n.value_paise ?? 0) > 0)
      .reduce((sum, n) => sum + (n.value_paise ?? 0), 0);

    // Monthly Cashflow.
    //
    // M10-A3: this was `transactions.slice(0, 30)` labelled "Monthly
    // Cashflow" — 30 arbitrary transactions, ordered by whatever order the
    // backend returned them, presented as a month. The label is only honest if
    // the transactions are actually bucketed by their own calendar month, so
    // that is what happens now; the most recent month in the graph is the one
    // reported and its bounds are stated in the label.
    const monthly = bucketLatestMonth(transactions);

    // Investment Return: mean of holding change percentages (a ratio, not money)
    const investmentReturn = holdings.length > 0
      ? mean(holdings.map(n => num(n.metadata?.change_percent)))
      : 0;

    // Debt Ratio: Total loans / total assets (a ratio, not money)
    const totalLoans = loans.reduce((sum, n) => sum + Math.abs(n.value_paise ?? 0), 0);
    const debtRatio = netWorth > 0 ? (totalLoans / netWorth) * 100 : 0;

    // Forecast Confidence: mean of the forecast nodes' own confidence
    const forecastConfidence = forecasts.length > 0
      ? mean(forecasts.map(n => num(n.confidence)))
      : 0;

    // Automation Success: mean of the behaviour score nodes' own confidence
    const behaviourScores = graph.nodes.filter(n => n.type === 'behaviour_score');
    const automationSuccess = behaviourScores.length > 0
      ? mean(behaviourScores.map(n => num(n.confidence)))
      : 0;

    // M10-A3: the previous version attached hardcoded period-over-period
    // deltas and confidences to every metric (`deltaPaise: 1820000, //
    // Placeholder`, `confidence: 97`, and so on). Those numbers were invented
    // and rendered as measured financial movement: the Command Center told the
    // user net worth was up ₹18,200 (+2.8%) at 97% confidence on every render,
    // with no data behind any of it. `deltaPaise` / `deltaPercent` are now
    // omitted entirely — the graph carries no prior-period balance for accounts
    // or loans, so there is no real change to report — and `confidence` is taken
    // from the nodes that produced the value instead of a literal.
    return [
      {
        id: 'net-worth',
        label: 'Net Worth',
        value: netWorth,
        format: 'money',
        nodeId: accounts[0]?.id,
      },
      {
        id: 'liquidity',
        label: 'Liquidity',
        value: liquidity,
        format: 'money',
        nodeId: accounts.find(a => (a.value_paise ?? 0) > 0)?.id,
      },
      {
        id: 'monthly-cashflow',
        label: monthly.label,
        value: monthly.netPaise,
        format: 'money',
        confidence: monthly.confidence,
        nodeId: monthly.nodeId,
      },
      {
        id: 'investment-return',
        label: 'Investment Return',
        value: investmentReturn,
        format: 'percent',
        nodeId: investments[0]?.id,
      },
      {
        id: 'debt-ratio',
        label: 'Debt Ratio',
        value: debtRatio,
        format: 'percent',
        nodeId: loans[0]?.id,
      },
      {
        id: 'forecast-confidence',
        label: 'Forecast Confidence',
        value: forecastConfidence,
        format: 'number',
        precision: 0,
        nodeId: forecasts[0]?.id,
      },
      {
        id: 'automation-success',
        label: 'Automation Success',
        value: automationSuccess,
        format: 'number',
        precision: 0,
        nodeId: behaviourScores[0]?.id,
      },
    ] as MetricData[];
  }, [graph]);

  // Handle metric click
  const handleMetricClick = useCallback((metric: MetricData) => {
    if (metric.nodeId) {
      onMetricSelect?.(metric.nodeId);
    }
  }, [onMetricSelect]);

  return (
    <Surface variant="timeline" density="none" className={cn('px-3 py-2', className)}>
      <div className="flex items-center justify-between gap-4">
        {metrics.map(metric => (
          <button
            key={metric.id}
            onClick={() => handleMetricClick(metric)}
            className="flex-1 min-w-0 cursor-pointer rounded-[var(--radius-sm)] p-2 hover:bg-[var(--surface-interactive)] transition-colors"
          >
            <div className="flex flex-col items-center gap-1">
              <span className="fin-caption text-[var(--text-tertiary)]">{metric.label}</span>
              <div className="flex items-center gap-1.5">
                <MetricTile
                  label=""
                  value={metric.value}
                  valuePaise={metric.format === 'money' ? metric.value : undefined}
                  format={metric.format}
                  precision={metric.precision}
                  change={metric.deltaPaise}
                  changePercent={metric.deltaPercent}
                  className="p-0"
                />
                {metric.confidence !== undefined && (
                  <ConfidenceBadge confidence={metric.confidence} showLabel={false} />
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
    </Surface>
  );
}