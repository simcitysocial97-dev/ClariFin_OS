/**
 * Selection Index - Central export for selection types and components
 */

export { SelectionCheckbox } from '@/components/selection/selection-checkbox';
export type { SelectionState, SelectionMode, SelectionAction, SelectionSummary } from './types';

// ===== Selection Runtime =====
export {
  SelectionRuntime,
  selectionRuntime,
} from './selection-runtime';
