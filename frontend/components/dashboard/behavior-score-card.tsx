'use client';

import { ChartContainer } from '@/components/ui/chart-container';
import { useBehaviorScore } from '@/lib/hooks/use-behavior-score';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

// Score color mapping
const getScoreColor = (score: number) => {
  if (score >= 81) return 'text-green-600';
  if (score >= 66) return 'text-blue-600';
  if (score >= 41) return 'text-amber-600';
  return 'text-red-600';
};

const getRingColor = (score: number) => {
  if (score >= 81) return 'stroke-green-500';
  if (score >= 66) return 'stroke-blue-500';
  if (score >= 41) return 'stroke-amber-500';
  return 'stroke-red-500';
};

// Component bar
function ComponentBar({ label, value, invert = false }: { label: string; value: number; invert?: boolean }) {
  const displayValue = invert ? 1 - value : value;
  const percentage = Math.round(displayValue * 100);
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{percentage}%</span>
      </div>
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div 
          className={cn(
            "h-full rounded-full transition-all",
            displayValue >= 0.7 ? "bg-green-500" :
            displayValue >= 0.4 ? "bg-amber-500" : "bg-red-500"
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export function BehaviorScoreCard() {
  const { data, isLoading, isError, refetch } = useBehaviorScore();

  const isEmpty = !data || data.financial_health_score === undefined;

  return (
    <ChartContainer
      isLoading={isLoading}
      isError={isError}
      isEmpty={isEmpty}
      onRetry={refetch}
      title="Financial Health Score"
    >
      {data && (
        <div className="space-y-4">
          {/* Score display with ring */}
          <div className="flex items-center justify-center">
            <div className="relative">
              <svg className="w-32 h-32" viewBox="0 0 100 100">
                {/* Background ring */}
                <circle
                  className="stroke-muted"
                  cx="50"
                  cy="50"
                  r="45"
                  strokeWidth="8"
                  fill="none"
                />
                {/* Progress ring */}
                <circle
                  className={cn("transition-all", getRingColor(data.financial_health_score))}
                  cx="50"
                  cy="50"
                  r="45"
                  strokeWidth="8"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${(data.financial_health_score / 100) * 283} 283`}
                  transform="rotate(-90 50 50)"
                />
                {/* Score text */}
                <text
                  x="50"
                  y="50"
                  dominantBaseline="middle"
                  textAnchor="middle"
                  className={cn("text-3xl font-bold", getScoreColor(data.financial_health_score))}
                >
                  {Math.round(data.financial_health_score)}
                </text>
              </svg>
            </div>
          </div>

          {/* Component scores */}
          <div className="space-y-2">
            <ComponentBar label="Savings Discipline" value={data.components.savings_discipline} />
            <ComponentBar label="Habit Stability" value={data.components.habit_stability} />
            <ComponentBar label="Impulsivity" value={data.components.impulsivity} invert />
          </div>

          {/* Risk flags */}
          <div className="flex flex-wrap gap-1.5">
            {data.risk_flags.india_specific.loan_app_pattern_flag && (
              <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                Loan App Activity
              </Badge>
            )}
            {data.risk_flags.high_impulsivity && (
              <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                High Impulsivity
              </Badge>
            )}
            {data.risk_flags.high_stress && (
              <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                Financial Stress
              </Badge>
            )}
            {data.risk_flags.low_savings && (
              <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                Low Savings
              </Badge>
            )}
          </div>

          {/* Summary */}
          <p className="text-xs text-muted-foreground text-center mt-2">
            {data.summary}
          </p>
        </div>
      )}
    </ChartContainer>
  );
}