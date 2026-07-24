/**
 * Scenario Engine - Stage 8C Financial OS Visual System
 *
 * Financial scenario comparison visualization.
 */

'use client';

import { useMemo } from 'react';
import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';

// ===== Scenario Item =====
export interface ScenarioItem {
  id: string;
  label: string;
  valuePaise: number;
  baselinePaise: number;
  probability?: number;
}

// ===== Props =====
interface ScenarioEngineProps {
  scenarios: ScenarioItem[];
  className?: string;
}

// ===== Scenario Engine Component =====
export function ScenarioEngine({
  scenarios,
  className,
}: ScenarioEngineProps) {
  const sortedScenarios = useMemo(() => {
    return [...scenarios].sort((a, b) => b.probability ?? 0 - (a.probability ?? 0));
  }, [scenarios]);

  if (sortedScenarios.length === 0) {
    return (
      <div className={className}>
        <p className="text-gray-500 text-sm">No scenario data available</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {sortedScenarios.map((scenario) => {
        const variance = scenario.valuePaise - scenario.baselinePaise;
        const isPositive = variance >= 0;

        return (
          <div key={scenario.id} className="p-3 border rounded-md">
            <div className="flex justify-between items-start">
              <p className="text-sm font-medium">{scenario.label}</p>
              {scenario.probability !== undefined && (
                <p className="text-xs text-gray-500">
                  {scenario.probability.toFixed(0)}% likely
                </p>
              )}
            </div>

            <div className="mt-2 space-y-1">
              <div className="flex justify-between">
                <span className="text-xs text-gray-500">Projected</span>
                <span className="text-sm font-mono">{formatINR(scenario.valuePaise)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-gray-500">Baseline</span>
                <span className="text-sm font-mono">{formatINR(scenario.baselinePaise)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-gray-500">Variance</span>
                <span className={cn(
                  'text-sm font-mono',
                  isPositive ? 'text-green-600' : 'text-red-600'
                )}>
                  {isPositive ? '+' : ''}{formatINR(variance)}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}