/**
 * useApiError Hook
 * ================
 * Custom hook for handling API errors consistently across all pages.
 * 
 * Usage:
 *   const { error, handleError, clearError } = useApiError();
 *   
 *   try {
 *     await fetchData();
 *   } catch (err) {
 *     handleError(err);
 *   }
 */

'use client';

import { useState, useCallback } from 'react';
import { ApiError } from '../api/client';

/**
 * Structured API error state
 */
export interface ApiErrorState {
  /** Human-readable error message */
  message: string;
  /** Machine-readable error code */
  errorCode: string;
  /** HTTP status code (0 for client-side errors) */
  status: number;
  /** Technical detail or stack trace */
  detail: string | null;
  /** API path that caused the error (if available) */
  path?: string;
  /** Timestamp when error occurred */
  timestamp?: string;
}

/**
 * Hook for handling API errors consistently
 * 
 * @returns Object containing error state and handler functions
 */
export function useApiError() {
  const [error, setError] = useState<ApiErrorState | null>(null);

  /**
   * Process an error and update the error state
   * 
   * Handles:
   * - ApiError instances (from our API client)
   * - Generic Error instances
   * - Unknown error types
   */
  const handleError = useCallback((err: unknown): void => {
    if (err instanceof ApiError) {
      setError({
        message: err.message,
        errorCode: err.errorCode,
        status: err.status,
        detail: err.detail,
        path: err.path,
        timestamp: err.timestamp,
      });
    } else if (err instanceof Error) {
      setError({
        message: err.message,
        errorCode: 'CLIENT_ERROR',
        status: 0,
        detail: err.stack ?? null,
      });
    } else if (typeof err === 'string') {
      setError({
        message: err,
        errorCode: 'CLIENT_ERROR',
        status: 0,
        detail: null,
      });
    } else {
      setError({
        message: 'An unexpected error occurred',
        errorCode: 'UNKNOWN',
        status: 0,
        detail: String(err),
      });
    }
  }, []);

  /**
   * Clear the current error state
   */
  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  /**
   * Check if the current error is a specific type
   */
  const isErrorCode = useCallback((code: string): boolean => {
    return error?.errorCode === code;
  }, [error]);

  /**
   * Check if the error is a network/client error
   */
  const isNetworkError = useCallback((): boolean => {
    return error?.status === 0 || error?.errorCode === 'CLIENT_ERROR';
  }, [error]);

  /**
   * Check if the error is a server error (5xx)
   */
  const isServerError = useCallback((): boolean => {
    return error !== null && error.status >= 500;
  }, [error]);

  /**
   * Check if the error is a not found error (404)
   */
  const isNotFoundError = useCallback((): boolean => {
    return error?.status === 404 || error?.errorCode === 'NOT_FOUND';
  }, [error]);

  /**
   * Check if the error is a validation error (422)
   */
  const isValidationError = useCallback((): boolean => {
    return error?.status === 422 || error?.errorCode === 'VALIDATION_ERROR';
  }, [error]);

  return {
    /** Current error state or null if no error */
    error,
    /** Process an error and update state */
    handleError,
    /** Clear the current error */
    clearError,
    /** Check if error matches a specific error code */
    isErrorCode,
    /** Check if this is a network/client error */
    isNetworkError,
    /** Check if this is a server error (5xx) */
    isServerError,
    /** Check if this is a not found error (404) */
    isNotFoundError,
    /** Check if this is a validation error (422) */
    isValidationError,
  };
}

/**
 * Convenience hook that also provides a retry wrapper
 * 
 * Usage:
 *   const { execute, error, clearError, isLoading } = useApiCall(fetchData);
 *   
 *   // Call execute() to run the function with automatic error handling
 */
export function useApiCall<TArgs extends unknown[], TReturn>(
  apiFunction: (...args: TArgs) => Promise<TReturn>
) {
  const { error, handleError, clearError } = useApiError();
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<TReturn | null>(null);

  const execute = useCallback(
    async (...args: TArgs): Promise<TReturn | null> => {
      setIsLoading(true);
      clearError();
      
      try {
        const result = await apiFunction(...args);
        setData(result);
        return result;
      } catch (err) {
        handleError(err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [apiFunction, clearError, handleError]
  );

  return {
    /** Execute the API call with automatic error handling */
    execute,
    /** Result data from successful call */
    data,
    /** Current error if call failed */
    error,
    /** Clear error state */
    clearError,
    /** Whether call is in progress */
    isLoading,
  };
}
