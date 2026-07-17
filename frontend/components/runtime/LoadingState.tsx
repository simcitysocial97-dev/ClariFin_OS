/**
 * LoadingState - Loading state component with multiple variants
 *
 * Supports: spinner, skeleton, inline, fullscreen, compact
 */

import type { ReactNode } from 'react'
import { Loader2 } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export type LoadingVariant = 'spinner' | 'skeleton' | 'inline' | 'fullscreen' | 'compact'

interface LoadingStateProps {
  variant?: LoadingVariant
  message?: string
  className?: string
  /** For skeleton variant - number of rows to show */
  rows?: number
  /** For inline variant - custom content */
  children?: ReactNode
}

export function LoadingState({
  variant = 'spinner',
  message = 'Loading...',
  className,
  rows = 3,
  children,
}: LoadingStateProps) {
  switch (variant) {
    case 'spinner':
      return (
        <div
          className={cn('flex flex-col items-center justify-center py-12', className)}
          role="status"
          aria-label={message}
        >
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden="true" />
          <p className="mt-3 text-sm text-muted-foreground">{message}</p>
        </div>
      )

    case 'skeleton':
      return (
        <div className={cn('space-y-3', className)}>
          {Array.from({ length: rows }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
      )

    case 'inline':
      return (
        <div
          className={cn('flex items-center gap-2', className)}
          role="status"
          aria-label={message}
        >
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          {children ?? <span className="text-sm text-muted-foreground">{message}</span>}
        </div>
      )

    case 'fullscreen':
      return (
        <div
          className={cn(
            'fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm',
            className
          )}
          role="status"
          aria-label={message}
        >
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-12 w-12 animate-spin text-primary" aria-hidden="true" />
            <p className="text-lg text-muted-foreground">{message}</p>
          </div>
        </div>
      )

    case 'compact':
      return (
        <div
          className={cn('flex items-center justify-center py-4', className)}
          role="status"
          aria-label={message}
        >
          <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
        </div>
      )

    default:
      return null
  }
}