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

// ===== Metric Data =====
export interface MetricData {
  id: MetricType;
  label: string;
  valuePaise: number;
  deltaPaise?: number;
  deltaPercent?: number;
  confidence: number;
  nodeId?: string;
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

    // Monthly Cashflow: Sum of recent transactions
    const monthlyCashflow = transactions
      .slice(0, 30)
      .reduce((sum, n) => sum + (n.value_paise ?? 0), 0);

    // Investment Return: Average of holding changes
    const investmentReturn = holdings.length > 0
      ? holdings.reduce((sum, n) => sum + ((n.metadata?.change_percent as number) ?? 0), 0) / holdings.length
      : 0;

    // Debt Ratio: Total loans / total assets
    const totalLoans = loans.reduce((sum, n) => sum + Math.abs(n.value_paise ?? 0), 0);
    const debtRatio = netWorth > 0 ? (totalLoans / netWorth) * 100 : 0;

    // Forecast Confidence: Average of forecast confidences
    const forecastConfidence = forecasts.length > 0
      ? forecasts.reduce((sum, n) => sum + (n.confidence ?? 0), 0) / forecasts.length
      : 0;

    // Automation Success: Based on behaviour scores
    const behaviourScores = graph.nodes.filter(n => n.type === 'behaviour_score');
    const automationSuccess = behaviourScores.length > 0
      ? behaviourScores.reduce((sum, n) => sum + (n.confidence ?? 0), 0) / behaviourScores.length
      : 0;

    return [
      {
        id: 'net-worth',
        label: 'Net Worth',
        valuePaise: netWorth,
        deltaPaise: 1820000, // Placeholder
        deltaPercent: 2.8,
        confidence: 97,
        nodeId: accounts[0]?.id,
      },
      {
        id: 'liquidity',
        label: 'Liquidity',
        valuePaise: liquidity,
        deltaPaise: 450000,
        deltaPercent: 1.2,
        confidence: 95,
        nodeId: accounts.find(a => (a.value_paise ?? 0) > 0)?.id,
      },
      {
        id: 'monthly-cashflow',
        label: 'Monthly Cashflow',
        valuePaise: monthlyCashflow,
        deltaPaise: -120000,
        deltaPercent: -3.5,
        confidence: 88,
        nodeId: transactions[0]?.id,
      },
      {
        id: 'investment-return',
        label: 'Investment Return',
        valuePaise: Math.round(investmentReturn * 10000), // Convert to paise-like value
        deltaPaise: 250000,
        deltaPercent: 1.5,
        confidence: 82,
        nodeId: investments[0]?.id,
      },
      {
        id: 'debt-ratio',
        label: 'Debt Ratio',
        valuePaise: Math.round(debtRatio * 10000), // Convert to paise-like value
        deltaPaise: -50000,
        deltaPercent: -0.8,
        confidence: 90,
        nodeId: loans[0]?.id,
      },
      {
        id: 'forecast-confidence',
        label: 'Forecast Confidence',
        valuePaise: Math.round(forecastConfidence * 10000),
        deltaPaise: 0,
        deltaPercent: 0,
        confidence: Math.round(forecastConfidence),
        nodeId: forecasts[0]?.id,
      },
      {
        id: 'automation-success',
        label: 'Automation Success',
        valuePaise: Math.round(automationSuccess * 10000),
        deltaPaise: 0,
        deltaPercent: 0,
        confidence: Math.round(automationSuccess),
        nodeId: behaviourScores[0]?.id,
      },
    ];
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
                  value={metric.valuePaise}
                  valuePaise={metric.valuePaise}
                  change={metric.deltaPaise}
                  changePercent={metric.deltaPercent}
                  className="p-0"
                />
                <ConfidenceBadge confidence={metric.confidence} showLabel={false} />
              </div>
            </div>
          </button>
        ))}
      </div>
    </Surface>
  );
}