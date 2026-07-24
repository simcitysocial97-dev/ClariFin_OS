/**
 * Wellness Radar - Stage 4 Behaviour Intelligence Workspace
 *
 * Displays a radar chart of financial wellness dimensions.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Radar } from 'lucide-react';
import type { WellnessRadarViewModel } from '@/types/behaviour-view-model';

/**
 * Wellness Radar Props
 */
interface WellnessRadarProps {
  wellnessRadar: WellnessRadarViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Wellness Radar Component
 *
 * Shows a visual representation of financial wellness across multiple dimensions.
 */
export function WellnessRadar({ wellnessRadar, loading, error }: WellnessRadarProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-48 w-full" />
            <div className="grid grid-cols-3 gap-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-4" />
              ))}
            </div>
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
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load wellness radar</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!wellnessRadar || wellnessRadar.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No wellness data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Radar className="h-5 w-5" />
          Wellness Radar
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Radar Visualization Placeholder */}
          <div className="relative h-48 flex items-center justify-center">
            <svg viewBox="0 0 200 200" className="w-full h-full max-w-48">
              {/* Radar grid lines */}
              {[1, 2, 3, 4, 5].map((level) => (
                <polygon
                  key={level}
                  points="100,100 100,20 170,50 100,180 30,50"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="0.5"
                  strokeOpacity={0.1 + level * 0.1}
                />
              ))}
              
              {/* Radar data polygon */}
              {(() => {
                const points = wellnessRadar.map((item, index) => {
                  const angle = (index * 2 * Math.PI) / wellnessRadar.length;
                  const radius = 60 * (item.score / item.max_score);
                  const x = 100 + radius * Math.cos(angle - Math.PI / 2);
                  const y = 100 + radius * Math.sin(angle - Math.PI / 2);
                  return `${x},${y}`;
                });
                return (
                  <polygon
                    points={points.join(' ')}
                    fill="rgba(99, 103, 241, 0.3)"
                    stroke="rgb(99, 103, 241)"
                    strokeWidth="2"
                  />
                );
              })()}
            </svg>
          </div>

          {/* Dimension Scores */}
          <div className="grid grid-cols-2 gap-2">
            {wellnessRadar.map((item) => (
              <div key={item.dimension} className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{item.dimension}</span>
                <span className="font-medium">
                  {((item.score / item.max_score) * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}