'use client';

import { ChartContainer } from '@/components/ui/chart-container';
import { ExplainButton } from '@/components/ui/explain-button';
import { useBehaviorScore } from '@/lib/hooks/use-behavior-score';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { WELLNESS_SCORE_DOCUMENTED_MAX } from '@/lib/schemas/behavior-score';

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

  // The score is rendered exactly as the authority states it.
  //
  // M10-A3: this read `financial_health_score ?? score` and then applied a
  // `> 100 ? /100 : ` basis-point guess. The `??` silently preferred a field
  // that `GET /api/v1/behaviour/wellness-score` does not return at all (it has
  // no `financial_health_score` key, so the fallback always resolved to
  // `score`), and the guess is how one payload produced different numbers on
  // /dashboard and /behaviour.
  //
  // Neither rescaling is adopted. `WellnessScoreResponse.score` is documented
  // 0-100 but is observed emitting 7561.45 against real data, because the
  // backend stores an already-0-100 value multiplied by 10000 again and reads
  // it back unscaled (`lib/schemas/behavior-score.ts` documents this in full).
  // The console does not correct a value it was given: it shows the score, and
  // when the score is outside the documented range the ring is not filled from
  // it and the discrepancy is stated, so the dashboard cannot quietly disagree
  // with the authority the way it did.
  const healthScore = data?.score ?? 0;
  const scoreInDocumentedRange = healthScore <= WELLNESS_SCORE_DOCUMENTED_MAX;
  const ringPercentage = scoreInDocumentedRange ? healthScore : 0;
  const isEmpty = !data;

  return (
    <div className="w-full">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">Financial Health Score</h3>
        <ExplainButton
          title="Financial Health Score"
          explanation="Your financial behavior score (0-100) based on savings discipline, habit stability, and spending patterns. Higher scores indicate healthier financial habits."
        />
      </div>
      <ChartContainer
        isLoading={isLoading}
        isError={isError}
        isEmpty={isEmpty}
        onRetry={refetch}
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
                  {/* Progress ring.
                      M10-A3: `healthScore / 100` with an out-of-contract score
                      produced a dasharray far longer than the 283 circumference,
                      so the ring drew multiple overlapping arcs. The fill is
                      clamped to the documented range and the value itself is
                      still shown verbatim, with a note below. */}
                  <circle
                    className={cn(
                      "transition-all",
                      scoreInDocumentedRange ? getRingColor(healthScore) : "stroke-muted-foreground/40",
                    )}
                    cx="50"
                    cy="50"
                    r="45"
                    strokeWidth="8"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={`${(ringPercentage / 100) * 283} 283`}
                    transform="rotate(-90 50 50)"
                  />
                  {/* Score text */}
                  <text
                    x="50"
                    y="50"
                    dominantBaseline="middle"
                    textAnchor="middle"
                    className={cn(
                      "text-3xl font-bold",
                      scoreInDocumentedRange ? getScoreColor(healthScore) : "fill-muted-foreground",
                    )}
                  >
                    {Math.round(healthScore)}
                  </text>
                </svg>
              </div>
            </div>

            {!scoreInDocumentedRange && (
              <p
                data-testid="dashboard-score-out-of-range"
                className="text-xs text-amber-600 text-center"
              >
                Reported score {healthScore} is outside the documented 0–
                {WELLNESS_SCORE_DOCUMENTED_MAX} range, so the ring is not filled from it.
              </p>
            )}

            {/* Component scores */}
            <div className="space-y-2">
              <ComponentBar label="Savings Discipline" value={data.components.savings_discipline ?? 0.5} />
              <ComponentBar label="Habit Stability" value={data.components.habit_stability ?? 0.5} />
              <ComponentBar label="Impulsivity" value={data.components.impulsivity ?? 0.5} invert />
            </div>

            {/* Risk flags */}
            <div className="flex flex-wrap gap-1.5">
              {data.risk_flags?.loan_app_pattern_flag && (
                <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                  Loan App Activity
                </Badge>
              )}
              {data.risk_flags?.high_impulsivity && (
                <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                  High Impulsivity
                </Badge>
              )}
              {data.risk_flags?.high_stress && (
                <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                  Financial Stress
                </Badge>
              )}
              {data.risk_flags?.low_savings && (
                <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                  Low Savings
                </Badge>
              )}
            </div>

            {/* Summary */}
            <p className="text-xs text-muted-foreground text-center mt-2">
              {data.summary ?? 'Continue tracking your financial transactions for better insights.'}
            </p>
          </div>
        )}
      </ChartContainer>
    </div>
  );
}