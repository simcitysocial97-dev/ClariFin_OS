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

  // Get component scores by name from the components array
  // Score is already converted to 0-100 range by the mapper
  const getComponentScore = (name: string): number => {
    const component = data?.components.find((c) => c.name === name);
    return component ? component.score / 100 : 0; // Convert from 0-100 to ratio (0-1)
  };

  const isEmpty = !data;

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
                  className={cn("transition-all", getRingColor(data.score))}
                  cx="50"
                  cy="50"
                  r="45"
                  strokeWidth="8"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${(data.score / 100) * 283} 283`}
                  transform="rotate(-90 50 50)"
                />
                {/* Score text */}
                <text
                  x="50"
                  y="50"
                  dominantBaseline="middle"
                  textAnchor="middle"
                  className={cn("text-3xl font-bold", getScoreColor(data.score))}
                >
                  {Math.round(data.score)}
                </text>
              </svg>
            </div>
          </div>

          {/* Component scores */}
          <div className="space-y-2">
            <ComponentBar label="Savings Discipline" value={getComponentScore('savings_behaviour')} />
            <ComponentBar label="Habit Stability" value={getComponentScore('resilience')} />
            <ComponentBar label="Impulsivity" value={getComponentScore('credit_behaviour')} invert />
          </div>

          {/* Band indicator */}
          <div className="flex justify-center">
            <Badge variant="outline" className="text-xs">
              {data.band}
            </Badge>
          </div>
        </div>
      )}
    </ChartContainer>
  );
}