/**
 * Forecast Filters - Stage 4 Forecast Intelligence Workspace
 *
 * Filter forecast by horizon and scenarios.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Filter, X } from 'lucide-react';

/**
 * Forecast Filters Props
 */
interface ForecastFiltersProps {
  horizon: number;
  scenarios: string[];
  onHorizonChange: (horizon: number) => void;
  onScenariosChange: (scenarios: string[]) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

/**
 * Available scenario options
 */
const SCENARIO_OPTIONS = ['conservative', 'moderate', 'aggressive'];

/**
 * Forecast Filters Component
 */
export function ForecastFilters({
  horizon,
  scenarios,
  onHorizonChange,
  onScenariosChange,
  onClearFilters,
  onApplyFilters,
}: ForecastFiltersProps) {
  const hasActiveFilters = horizon > 0 || scenarios.length > 0;

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-gray-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <h3 className="font-medium">Filters</h3>
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="text-xs"
          >
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Horizon Filter */}
        <div className="space-y-2">
          <Label htmlFor="horizon">Forecast Horizon (months)</Label>
          <Input
            id="horizon"
            type="number"
            placeholder="e.g., 12, 24, 36"
            value={horizon || ''}
            onChange={(e) => onHorizonChange(parseInt(e.target.value) || 0)}
          />
        </div>

        {/* Scenarios Filter */}
        <div className="space-y-2">
          <Label>Scenarios</Label>
          <div className="flex flex-wrap gap-1">
            {SCENARIO_OPTIONS.map((scenario) => (
              <button
                key={scenario}
                onClick={() => {
                  const newScenarios = scenarios.includes(scenario)
                    ? scenarios.filter((s) => s !== scenario)
                    : [...scenarios, scenario];
                  onScenariosChange(newScenarios);
                }}
                className={`px-2 py-1 text-xs rounded ${
                  scenarios.includes(scenario)
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                aria-pressed={scenarios.includes(scenario)}
              >
                {scenario}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button onClick={onApplyFilters} size="sm">
          Apply Filters
        </Button>
      </div>
    </div>
  );
}