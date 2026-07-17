/**
 * EmptyState - Empty state component with illustration slot, CTA, and optional explainability
 */

import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  title?: string
  description?: string
  icon?: ReactNode
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
  /** Optional explainability content */
  explanation?: ReactNode
}

export function EmptyState({
  title = 'No data available',
  description = 'There is nothing to display right now.',
  icon,
  action,
  className,
  explanation,
}: EmptyStateProps) {
  return (
    <Card className={cn('border-dashed', className)}>
      <CardContent className="flex flex-col items-center justify-center py-16 px-6 text-center">
        <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center mb-6">
          <div className="text-muted-foreground" aria-hidden="true">
            {icon ?? <Inbox className="h-8 w-8" />}
          </div>
        </div>

        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-muted-foreground max-w-md mb-6">{description}</p>

        {explanation && <div className="w-full mb-4">{explanation}</div>}

        {action && (
          <Button onClick={action.onClick} className="mt-2">
            {action.label}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}