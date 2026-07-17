/**
 * Explainability Runtime - Public API
 */

// Contracts
export type {
  SourceType,
  SourceReference,
  SourceCollection,
  EvidenceType,
  EvidenceValue,
  Evidence,
  EvidenceCollection,
  CalculationOperation,
  CalculationStep,
  CalculationSteps,
  ConfidenceBps,
  Confidence,
  Explanation,
  RecommendationExplanation,
  ExplanationCollection,
} from './contracts'

// Utilities
export { createExplanation, createRecommendationExplanation } from './createExplanation'
export { mergeEvidence } from './mergeEvidence'
export { sortEvidence } from './sortEvidence'
export { confidenceToBadge, getBadgeClass } from './confidenceToBadge'
export type { BadgeLevel } from './confidenceToBadge'
export { groupEvidence } from './groupEvidence'
export { flattenExplanation, flattenRecommendationExplanation } from './flattenExplanation'
export type { FlattenedItem } from './flattenExplanation'

// Validation
export { isValidConfidenceBps, createConfidence } from './contracts/Confidence'

// Hooks
export {
  useExplainability,
  useExplainabilityCollection,
  useRecommendationExplanation,
} from './useExplainability'
export type {
  ExplanationState,
  UseExplainabilityResult,
  UseExplainabilityCollectionResult,
  UseRecommendationExplanationResult,
} from './useExplainability'
