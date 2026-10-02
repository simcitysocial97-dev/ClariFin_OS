/**
 * Behaviour Score Card - Stage 4 Behaviour Intelligence Workspace
 *
 * Displays the overall financial health score.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Heart } from 'lucide-react';
import type { BehaviourScoreViewModel } from '@/types/behaviour-view-model';

/**
 * Behaviour Score Props
 */
interface BehaviourScoreProps {
  score: BehaviourScoreViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Behaviour Score Card Component
 *
 * Shows the overall financial health score with label and factors.
 */
export function BehaviourScore({ score, loading, error }: BehaviourScoreProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-16 w-16 rounded-full mx-auto" />
            <Skeleton className="h-4 w-24 mx-auto" />
            <Skeleton className="h-4 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-[var(--color-negative-600)]">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load score</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!score) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-[var(--text-tertiary)] text-sm">No score data available</p>
        </CardContent>
      </Card>
    );
  }

  // The wellness score is a 0-100 magnitude, not a basis-point quantity.
  //
  // M10-A3: this component divided the score by 100 and compared it against
  // 800/600 thresholds, i.e. it assumed basis points (0-10000). The authority
  // does not use that scale: `WellnessScoreResponse.score` is documented
  // "Wellness score between 0 and 100"
  // (backend/src/models/behaviour.py:31) and is produced by
  // `wellness_score * 100` clamped to `[0, 100]`
  // (backend/src/engines/behaviour_engine/wellness.py:83-85), after which
  // `classify_wellness_band` reads that same 0-100 value. Against a live score
  // of 100 the old code rendered "1.0%", the ring at 1% fill, the "Excellent"
  // band beside it, and always the negative colour because 800 is unreachable.
  // The same score on /dashboard rendered as 76 — the same payload, two
  // different answers on two screens.
  const percentage = score.score.toFixed(1);

  // Determine score color on the authoritative 0-100 scale.
  const scoreColor = score.score >= 70
    ? 'text-[var(--color-positive-600)]'
    : score.score >= 40
      ? 'text-[var(--color-warning-600)]'
      : 'text-[var(--color-negative-600)]';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Heart className="h-5 w-5" />
          Financial Health Score
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center space-y-4">
          {/* Score Circle */}
          <div className="relative inline-flex items-center justify-center">
            <svg className="w-24 h-24" viewBox="0 0 100 100">
              <circle
                className="text-gray-200"
                strokeWidth="8"
                stroke="currentColor"
                fill="transparent"
                r="42"
                cx="50"
                cy="50"
              />
              <circle
                className={scoreColor}
                strokeWidth="8"
                strokeDasharray="264"
                strokeDashoffset={264 - (264 * score.score) / 100}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                r="42"
                cx="50"
                cy="50"
              />
            </svg>
            <span className={`absolute text-2xl font-bold ${scoreColor}`} aria-label="Health score">
              {percentage}
            </span>
          </div>

          {/* Score Label */}
          <p className="text-lg font-medium" aria-label="Score label">
            {score.label}
          </p>

          {/* Factors */}
          {score.factors && score.factors.length > 0 && (
            <div className="pt-2">
              <p className="text-xs text-gray-500 mb-2">Key Factors</p>
              <ul className="text-xs text-left space-y-1">
                {score.factors.map((factor, index) => (
                  <li key={index} className="flex items-center gap-1">
                    <span className="w-1 h-1 bg-gray-400 rounded-full" />
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}