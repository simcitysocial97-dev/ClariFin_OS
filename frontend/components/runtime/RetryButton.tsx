/**
 * RetryButton - Reusable retry button for error/offline states
 */

import { RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface RetryButtonProps {
  onRetry: () => void
  label?: string
  className?: string
  size?: 'default' | 'sm' | 'lg' | 'icon' | 'xs'
}

export function RetryButton({
  onRetry,
  label = 'Try again',
  className,
  size = 'default',
}: RetryButtonProps) {
  return (
    <Button
      onClick={onRetry}
      variant="outline"
      size={size}
      className={cn('gap-2', className)}
      aria-label={label}
    >
      <RefreshCw className="h-4 w-4" aria-hidden="true" />
      {label}
    </Button>
  )
}