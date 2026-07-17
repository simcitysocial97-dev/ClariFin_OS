/**
 * DataStateWrapper - Reusable composition component for rendering queried data
 *
 * This is the ONLY approved pattern for rendering queried data.
 * It connects React Query → Runtime Adapter → Loading/Error/Empty runtime → Capability UI
 *
 * Never expose query flags (isLoading, isError, isFetching) to pages.
 */

import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { fromQuery } from '@/lib/runtime'
import { LoadingState } from './LoadingState'
import { ErrorState } from './ErrorState'
import { EmptyState } from './EmptyState'
import { OfflineState } from './OfflineState'
import { PermissionState } from './PermissionState'

/**
 * Override components for each state
 */
interface DataStateWrapperOverrides {
  /** Custom loading component */
  loading?: ReactNode
  /** Custom error component */
  error?: ReactNode
  /** Custom empty component */
  empty?: ReactNode
  /** Custom offline component */
  offline?: ReactNode
  /** Custom permission component */
  permission?: ReactNode
  /** Custom stale indicator (renders alongside data) */
  stale?: ReactNode
  /** Default fallback for unhandled states */
  fallback?: ReactNode
}

/**
 * Props for DataStateWrapper
 */
interface DataStateWrapperProps<T> extends DataStateWrapperOverrides {
  query: UseQueryResult<T, any>
  /** Content to render on success - render prop pattern */
  children?: (data: T) => ReactNode
  /** Alternative render prop (normalized with children) */
  render?: (data: T) => ReactNode
  /** Optional empty detection function */
  isEmpty?: (data: T) => boolean
  /** Optional loading variant */
  loadingVariant?: 'spinner' | 'skeleton' | 'inline' | 'fullscreen' | 'compact'
  /** Optional loading message */
  loadingMessage?: string
}

/**
 * Wraps TanStack Query result with appropriate runtime state components
 *
 * Priority:
 * 1. If override provided, use override component
 * 2. Otherwise, use default state component
 * 3. For success/stale, render children/render prop with data
 */
export function DataStateWrapper<T>({
  query,
  children,
  render,
  isEmpty,
  loadingVariant = 'spinner',
  loadingMessage,
  loading,
  error,
  empty,
  offline,
  permission,
  stale,
  fallback,
}: DataStateWrapperProps<T>) {
  // Normalize render and children - both are render props
  const renderProp = children ?? render

  // Convert query to runtime state
  const state = fromQuery(query, { isEmpty: isEmpty as ((data: unknown) => boolean) | undefined })

  // Handle each state with override support
  switch (state.state) {
    case 'loading':
      // If custom loading override provided, use it
      if (loading) {
        return <>{loading}</>
      }
      return (
        <LoadingState variant={loadingVariant} message={loadingMessage} />
      )

    case 'error':
      // If custom error override provided, use it
      if (error) {
        return <>{error}</>
      }
      return (
        <ErrorState
          title={state.title}
          description={state.description}
          error={state.error}
          onRetry={state.retry}
        />
      )

    case 'offline':
      // If custom offline override provided, use it
      if (offline) {
        return <>{offline}</>
      }
      return (
        <OfflineState
          title={state.title}
          description={state.description}
          onRetry={state.retry}
        />
      )

    case 'permission':
      // If custom permission override provided, use it
      if (permission) {
        return <>{permission}</>
      }
      return (
        <PermissionState
          title={state.title}
          description={state.description}
        />
      )

    case 'empty':
      // If custom empty override provided, use it
      if (empty) {
        return <>{empty}</>
      }
      return (
        <EmptyState
          title={state.title}
          description={state.description}
          action={state.retry ? { label: 'Refresh', onClick: state.retry } : undefined}
        />
      )

    case 'success':
      // Render with data
      if (state.data && renderProp) {
        return <>{renderProp(state.data)}</>
      }
      return null

    case 'stale':
      // Render data with optional stale indicator
      if (state.data && renderProp) {
        return (
          <>
            {stale && <div className="stale-indicator">{stale}</div>}
            {renderProp(state.data)}
          </>
        )
      }
      return null

    default:
      // Fallback for unknown states
      return fallback ? <>{fallback}</> : null
  }
}