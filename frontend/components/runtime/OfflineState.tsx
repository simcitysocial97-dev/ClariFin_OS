/**
 * OfflineState - Reusable offline state component
 *
 * Does NOT know about specific capabilities.
 */

import { WifiOff } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { RetryButton } from './RetryButton'
import { cn } from '@/lib/utils'

interface OfflineStateProps {
  title?: string
  description?: string
  onRetry?: () => void
  className?: string
}

export function OfflineState({
  title = 'You are offline',
  description = 'Check your connection and try again.',
  onRetry,
  className,
}: OfflineStateProps) {
  return (
    <Card className={cn('border-amber-200', className)}>
      <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
        <WifiOff className="h-12 w-12 text-amber-500 mb-4" aria-hidden="true" />

        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground mb-4 max-w-md">{description}</p>

        {onRetry && <RetryButton onRetry={onRetry} />}
      </CardContent>
    </Card>
  )
}