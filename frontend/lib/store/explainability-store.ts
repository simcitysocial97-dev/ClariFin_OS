/**
 * Explainability Store - Zustand store for explainability UI state
 *
 * Owns all UI state for the explainability drawer:
 * - selectedExplanation
 * - activeTab
 * - expandedSteps
 * - filters
 *
 * This is separate from lifecycle (managed by ExplainabilityProvider).
 */

import { create } from 'zustand'
import type { Explanation, RecommendationExplanation } from '../explainability'

/**
 * Tab types for the explainability drawer
 */
export type ExplainabilityTab = 'overview' | 'calculation' | 'evidence' | 'sources'

/**
 * Explainability store state
 */
interface ExplainabilityState {
  // Current explanation being displayed
  selectedExplanation: Explanation | null
  selectedRecommendation: RecommendationExplanation | null

  // UI state
  activeTab: ExplainabilityTab
  expandedSteps: Set<string>
  searchQuery: string

  // Actions
  setExplanation: (explanation: Explanation | null) => void
  setRecommendation: (recommendation: RecommendationExplanation | null) => void
  setActiveTab: (tab: ExplainabilityTab) => void
  toggleStep: (stepId: string) => void
  setSearchQuery: (query: string) => void
  reset: () => void
}

/**
 * Zustand store for explainability UI state
 */
export const useExplainabilityStore = create<ExplainabilityState>((set) => ({
  // Initial state
  selectedExplanation: null,
  selectedRecommendation: null,
  activeTab: 'overview',
  expandedSteps: new Set(),
  searchQuery: '',

  // Actions
  setExplanation: (explanation) =>
    set({
      selectedExplanation: explanation,
      selectedRecommendation: null,
      activeTab: 'overview',
      expandedSteps: new Set(),
    }),

  setRecommendation: (recommendation) =>
    set({
      selectedRecommendation: recommendation,
      selectedExplanation: null,
      activeTab: 'overview',
      expandedSteps: new Set(),
    }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  toggleStep: (stepId) =>
    set((state) => {
      const newExpanded = new Set(state.expandedSteps)
      if (newExpanded.has(stepId)) {
        newExpanded.delete(stepId)
      } else {
        newExpanded.add(stepId)
      }
      return { expandedSteps: newExpanded }
    }),

  setSearchQuery: (query) => set({ searchQuery: query }),

  reset: () =>
    set({
      selectedExplanation: null,
      selectedRecommendation: null,
      activeTab: 'overview',
      expandedSteps: new Set(),
      searchQuery: '',
    }),
}))