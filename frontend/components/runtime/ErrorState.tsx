/**
 * ErrorState - Error state component with retry and optional explainability
 *
 * Shows an "Explain" button when error contains an Explanation object.
 * Does NOT know about specific capabilities.
 */

'use client'

import type { ReactNode } from 'react'
import { AlertCircle, Info } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RetryButton } from './RetryButton'
import { useExplainabilityDrawer } from '@/components/explainability'
import { cn } from '@/lib/utils'
import type { Explanation } from '@/lib/explainability'

interface ErrorStateProps {
  title?: string
  description?: string
  error?: Error & { explanation?: Explanation }
  onRetry?: () => void
  retryLabel?: string
  className?: string
  /** Optional custom actions */
  actions?: ReactNode
  /** Optional explainability content (Explanation object) */
  explanation?: Explanation
}

export function ErrorState({
  title = 'Something went wrong',
  description,
  error,
  onRetry,
  retryLabel,
  className,
  actions,
  explanation,
}: ErrorStateProps) {
  const { showExplanation } = useExplainabilityDrawer()

  // Get explanation from either prop or error object
  const hasExplanation = explanation ?? error?.explanation

  const handleExplain = () => {
    if (hasExplanation) {
      showExplanation(hasExplanation)
    }
  }

  return (
    <Card className={cn('border-destructive/50', className)}>
      <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" aria-hidden="true" />

        <h3 className="text-lg font-semibold mb-2">{title}</h3>

        {description && (
          <p className="text-sm text-muted-foreground mb-4 max-w-md">{description}</p>
        )}

        {error && (
          <details className="w-full mb-4 text-left">
            <summary className="text-xs text-muted-foreground cursor-pointer hover:underline">
              Show details
            </summary>
            <pre className="mt-2 text-xs bg-muted p-3 rounded overflow-x-auto">
              {error.message}
            </pre>
          </details>
        )}

        <div className="flex gap-2">
          {onRetry && <RetryButton onRetry={onRetry} label={retryLabel} />}
          {hasExplanation && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExplain}
              aria-label="Explain error"
            >
              <Info className="h-4 w-4 mr-1" aria-hidden="true" />
              Explain
            </Button>
          )}
          {actions}
        </div>
      </CardContent>
    </Card>
  )
}