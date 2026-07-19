/**
 * Utilization Chart - Stage 4 Credit Cards Intelligence Workspace
 *
 * Visualizes credit card utilization as a bar chart.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import type { CreditCardsViewModel, UtilizationViewModel } from '@/types/credit-cards-view-model';

/**
 * Utilization Chart Props
 */
interface UtilizationChartProps {
  creditCards: CreditCardsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Utilization Bar Component
 */
function UtilizationBar({ utilization }: { utilization: UtilizationViewModel }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Card {utilization.card_id}</span>
        <span className="text-sm text-gray-500">{utilization.utilization_percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className={`h-4 rounded-full ${
            utilization.utilization_percentage > 80 ? 'bg-red-500' :
            utilization.utilization_percentage > 50 ? 'bg-yellow-500' : 'bg-green-500'
          }`}
          style={{ width: `${Math.min(utilization.utilization_percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

/**
 * Utilization Chart Component
 */
export function UtilizationChart({ creditCards, loading, error }: UtilizationChartProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-5 w-32" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
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
        <CardHeader>
          <CardTitle>Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load utilization data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!creditCards || !creditCards.utilization || creditCards.utilization.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No utilization data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Utilization</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {creditCards.utilization.map((utilization) => (
            <UtilizationBar key={utilization.card_id} utilization={utilization} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}