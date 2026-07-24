/**
 * Navigation Error Handling - Stage 3 Transaction Intelligence Workspace
 *
 * Utilities for handling navigation errors gracefully.
 */

/**
 * Navigation error types
 */
export type NavigationErrorType =
  | 'invalid_route'
  | 'missing_params'
  | 'unauthorized'
  | 'not_found'
  | 'server_error';

/**
 * Navigation error structure
 */
export interface NavigationError {
  type: NavigationErrorType;
  message: string;
  originalPath?: string;
}

/**
 * Create a navigation error
 */
export function createNavigationError(
  type: NavigationErrorType,
  message: string,
  originalPath?: string
): NavigationError {
  return { type, message, originalPath };
}

/**
 * Handle navigation error by redirecting to error page or showing error
 * Note: This function is intended to be used in client components with useRouter
 */
export function handleNavigationError(
  error: NavigationError,
  router: { push: (path: string) => void }
): void {
  // Log error for debugging
  console.error(`Navigation error [${error.type}]:`, error.message);

  // Redirect to error page with details
  const errorPath = `/transactions/error?type=${error.type}&message=${encodeURIComponent(error.message)}`;
  router.push(errorPath);
}

/**
 * Validate navigation path and return error if invalid
 */
export function validateNavigationPath(
  path: string,
  requiredParams: string[]
): NavigationError | null {
  const url = new URL(path, 'http://localhost');
  const searchParams = url.searchParams;

  for (const param of requiredParams) {
    if (!searchParams.has(param)) {
      return createNavigationError(
        'missing_params',
        `Missing required parameter: ${param}`,
        path
      );
    }
  }

  return null;
}

/**
 * Get user-friendly error message for navigation error
 */
export function getNavigationErrorMessage(error: NavigationError): string {
  switch (error.type) {
    case 'invalid_route':
      return 'The page you are trying to navigate to does not exist.';
    case 'missing_params':
      return 'Some required information is missing for navigation.';
    case 'unauthorized':
      return 'You do not have permission to access this page.';
    case 'not_found':
      return 'The requested page could not be found.';
    case 'server_error':
      return 'A server error occurred while navigating.';
    default:
      return 'An unexpected error occurred during navigation.';
  }
}

/**
 * Check if a navigation error is recoverable
 */
export function isNavigationErrorRecoverable(error: NavigationError): boolean {
  return error.type !== 'unauthorized' && error.type !== 'not_found';
}