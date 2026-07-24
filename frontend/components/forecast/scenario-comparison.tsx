/**
 * Scenario Comparison - Stage 4 Forecast Intelligence Workspace
 *
 * Displays comparison of forecast scenarios.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, BarChart3 } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { ForecastScenarioViewModel } from '@/types/forecast-view-model';

/**
 * Scenario Comparison Props
 */
interface ScenarioComparisonProps {
  scenarios: ForecastScenarioViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Scenario Comparison Component
 *
 * Shows a comparison of different forecast scenarios with probability and outcomes.
 */
export function ScenarioComparison({ scenarios, loading, error }: ScenarioComparisonProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
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
            <span className="text-sm">Failed to load scenarios</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!scenarios || scenarios.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No scenario data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Scenario Comparison
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {scenarios.map((scenario) => {
            // Get final projection
            const finalProjection = scenario.net_worth_projections[scenario.net_worth_projections.length - 1];
            const probability = (scenario.probability_bps / 100).toFixed(1);
            
            return (
              <div key={scenario.name} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">{scenario.name}</h3>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {probability}% probability
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-3">{scenario.description}</p>
                
                {finalProjection && (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-xs text-gray-500">Final Net Worth</p>
                      <p className="font-medium" aria-label="Final net worth">
                        {formatINR(finalProjection.projected_paise)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Confidence Range</p>
                      <p className="text-xs" aria-label="Confidence range">
                        {formatINR(finalProjection.lower_bound_paise)} - {formatINR(finalProjection.upper_bound_paise)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}