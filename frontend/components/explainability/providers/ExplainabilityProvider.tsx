/**
 * ExplainabilityProvider - Lifecycle management for explainability drawer
 *
 * Manages drawer open/close lifecycle.
 * Delegates state management to Zustand store.
 */

'use client'

import type { ReactNode } from 'react'
import { createContext, useContext, useCallback } from 'react'
import type { Explanation, RecommendationExplanation } from '@/lib/explainability'
import { useExplainabilityStore } from '@/lib/store/explainability-store'

/**
 * Explainability context for lifecycle
 */
interface ExplainabilityContextValue {
  isOpen: boolean
  open: () => void
  close: () => void
  showExplanation: (explanation: Explanation) => void
  showRecommendation: (recommendation: RecommendationExplanation) => void
}

const ExplainabilityContext = createContext<ExplainabilityContextValue | null>(null)

/**
 * Provider for explainability drawer lifecycle
 */
export function ExplainabilityProvider({ children }: { children: ReactNode }) {
  const { setExplanation, setRecommendation, reset } = useExplainabilityStore()

  const open = useCallback(() => {
    // Drawer is opened by setting an explanation
  }, [])

  const close = useCallback(() => {
    reset()
  }, [reset])

  const showExplanation = useCallback(
    (explanation: Explanation) => {
      setExplanation(explanation)
    },
    [setExplanation],
  )

  const showRecommendation = useCallback(
    (recommendation: RecommendationExplanation) => {
      setRecommendation(recommendation)
    },
    [setRecommendation],
  )

  return (
    <ExplainabilityContext.Provider
      value={{
        isOpen: true, // Will be derived from store state
        open,
        close,
        showExplanation,
        showRecommendation,
      }}
    >
      {children}
    </ExplainabilityContext.Provider>
  )
}

/**
 * Hook to access explainability context
 */
export function useExplainabilityContext() {
  const context = useContext(ExplainabilityContext)
  if (!context) {
    throw new Error('useExplainabilityContext must be used within ExplainabilityProvider')
  }
  return context
}