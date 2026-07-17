/**
 * Calculation Step - Single step in a calculation chain
 *
 * Represents an operation performed during a financial calculation.
 */

/**
 * Calculation operation types - enum for type safety
 */
export type CalculationOperation =
  | 'ADD'
  | 'SUBTRACT'
  | 'MULTIPLY'
  | 'DIVIDE'
  | 'AVERAGE'
  | 'LOOKUP'
  | 'FILTER'
  | 'GROUP'
  | 'MATCH'

/**
 * Single step in a calculation chain
 */
export interface CalculationStep {
  readonly stepId: string
  readonly description: string
  readonly operation: CalculationOperation
  readonly inputIds: string[]
  readonly outputId: string
  readonly order: number
}

/**
 * Calculation steps collection
 */
export interface CalculationSteps {
  readonly steps: CalculationStep[]
}
