/**
 * Navigation - Stage 3 Transaction Intelligence Workspace
 *
 * Public API exports for navigation utilities.
 */

export {
  getCategoryWorkspaceUrl,
  getCategoryWorkspaceUrlByName,
  hasCategoryNavigation,
} from './category-navigation';

export {
  getMerchantWorkspaceUrl,
  getMerchantWorkspaceUrlByName,
  hasMerchantNavigation,
} from './merchant-navigation';

export {
  getDateWorkspaceUrl,
  getMonthWorkspaceUrl,
  hasDateNavigation,
} from './date-navigation';

export {
  getAccountWorkspaceUrl,
  hasAccountNavigation,
} from './account-navigation';

export {
  getBalanceWorkspaceUrl,
  hasBalanceNavigation,
} from './balance-navigation';

export {
  getReconciliationWorkspaceUrl,
  hasReconciliationNavigation,
} from './reconciliation-navigation';

export {
  getImportWorkspaceUrl,
  hasImportNavigation,
} from './import-navigation';

export {
  getAdjustmentWorkspaceUrl,
  hasAdjustmentNavigation,
} from './adjustment-navigation';

// State persistence
export {
  useNavigationState,
  useSetNavigationState,
  useClearNavigationState,
  parseNavigationState,
  buildNavigationUrl,
} from './persistence';
export type { NavigationState } from './persistence';

// Keyboard shortcuts
export {
  useNavigationKeyboardShortcuts,
  isNavigationShortcut,
} from './keyboard';
export type { NavigationKeyboardShortcuts } from './keyboard';

// Error handling
export {
  createNavigationError,
  handleNavigationError,
  validateNavigationPath,
  getNavigationErrorMessage,
  isNavigationErrorRecoverable,
} from './error-handling';
export type { NavigationError, NavigationErrorType } from './error-handling';

// ===== Navigation Runtime =====
// Re-export NavigationRuntime from command-center as the canonical navigation runtime
export {
  NavigationRuntime,
  navigationRuntime,
  type NavigationTarget,
  type NavigationHistory,
} from '../command-center/navigation';
