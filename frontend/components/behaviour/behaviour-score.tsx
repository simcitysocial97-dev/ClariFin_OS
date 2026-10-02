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
import { WELLNESS_SCORE_DOCUMENTED_MAX } from '@/lib/schemas/behavior-score';

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

  // The score is rendered exactly as the authority states it.
  //
  // M10-A3: this component previously divided the score by 100 and compared it
  // against 800/600 thresholds, i.e. it assumed basis points, while
  // `lib/schemas/behavior-score.ts` separately claimed a 0-100 range. Against
  // the no-data fallback (`score: "100"`) that rendered "1.0%", the ring at 1%
  // fill, the "Excellent" band beside it, and always the negative colour
  // because 800 is unreachable.
  //
  // Neither belief is adopted here. The authority is observed emitting 7561.45
  // against real data (see the schema for the backend double-scaling that
  // causes it), and `classify_wellness_band` thresholds at 90/75/50/25, so the
  // band the response supplies is only meaningful while the score is inside the
  // documented 0-100 range. The console does not rescale a value it has been
  // given, so:
  //   - in range  -> the score and the authority's own band colours apply
  //   - out of range -> the score is shown, the ring is not filled from it, the
  //     colour is not derived from it, and the discrepancy is stated
  const inDocumentedRange = score.score <= WELLNESS_SCORE_DOCUMENTED_MAX;
  const percentage = inDocumentedRange ? score.score.toFixed(1) : String(score.score);

  // Determine score color on the documented 0-100 scale. An out-of-contract
  // score is never coloured as good or bad — the authority's band is not
  // trustworthy for it, so no verdict is implied.
  const scoreColor = !inDocumentedRange
    ? 'text-[var(--text-tertiary)]'
    : score.score >= 70
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
                strokeDashoffset={
                  inDocumentedRange ? 264 - (264 * score.score) / 100 : 264
                }
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

          {/* M10-A3: state the contract breach rather than silently rescaling
              the value or colouring it from a score the authority's own band
              thresholds cannot interpret. */}
          {!inDocumentedRange && (
            <p
              data-testid="behaviour-score-out-of-range"
              className="text-xs text-[var(--color-warning-600)]"
            >
              Reported score {score.score} is outside the documented 0–
              {WELLNESS_SCORE_DOCUMENTED_MAX} range, so the band and ring above
              are not derived from it.
            </p>
          )}

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