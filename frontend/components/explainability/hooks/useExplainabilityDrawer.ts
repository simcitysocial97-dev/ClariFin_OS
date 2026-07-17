/**
 * useExplainabilityDrawer - Hook for explainability drawer state
 *
 * Combines Zustand store with drawer lifecycle.
 */

import { useExplainabilityStore } from '@/lib/store/explainability-store'
import type { Explanation, RecommendationExplanation } from '@/lib/explainability'

/**
 * Hook for accessing and controlling the explainability drawer
 */
export function useExplainabilityDrawer() {
  const {
    selectedExplanation,
    selectedRecommendation,
    activeTab,
    expandedSteps,
    searchQuery,
    setExplanation,
    setRecommendation,
    setActiveTab,
    toggleStep,
    setSearchQuery,
    reset,
  } = useExplainabilityStore()

  const isOpen = selectedExplanation !== null || selectedRecommendation !== null

  const showExplanation = (explanation: Explanation) => {
    setExplanation(explanation)
  }

  const showRecommendation = (recommendation: RecommendationExplanation) => {
    setRecommendation(recommendation)
  }

  const close = () => {
    reset()
  }

  return {
    // State
    isOpen,
    activeTab,
    expandedSteps,
    searchQuery,
    selectedExplanation,
    selectedRecommendation,

    // Actions
    showExplanation,
    showRecommendation,
    close,
    setActiveTab,
    toggleStep,
    setSearchQuery,
  }
}