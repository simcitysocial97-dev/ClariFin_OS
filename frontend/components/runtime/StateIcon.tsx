/**
 * StateIcon - Maps RuntimeState to icon
 *
 * Uses the registry pattern - no switch statements duplicated elsewhere.
 */

import type { RuntimeState } from '@/lib/runtime'
import { getStateIcon } from '@/lib/runtime'

interface StateIconProps {
  state: RuntimeState
  className?: string
}

export function StateIcon({ state, className }: StateIconProps) {
  const icon = getStateIcon(state)

  if (!icon) return null

  return (
    <div className={className} aria-hidden="true">
      {icon}
    </div>
  )
}