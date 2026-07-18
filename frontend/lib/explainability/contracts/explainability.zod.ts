/**
 * Explainability Contracts - Shared Zod schemas for explanation validation
 *
 * These schemas are the canonical Zod definitions for explanation types.
 * Re-exported by other API contract files.
 */

import { z } from 'zod'

// Source reference schema - mirrors backend SourceReference
export const SourceReferenceSchema = z.object({
  // Source type classification
  type: z.enum([
    'statement',
    'account',
    'loan',
    'investment',
    'transaction',
    'recommendation_engine',
    'cashflow_engine',
    'behaviour_engine',
    'user_input',
  ]),

  // Source identifier
  id: z.union([z.string(), z.number()]),

  // Human-readable name
  name: z.string().nullable().optional(),

  // Source date (for statements)
  date: z.string().nullable().optional(),
})

// Evidence schema
export const EvidenceSchema = z.object({
  id: z.string(),
  type: z.enum(['data', 'calculation', 'source']),
  description: z.string(),
  value: z.union([z.number(), z.string(), z.boolean()]).nullable(),
  sourceId: z.union([z.string(), z.number()]).optional(),
})

// Calculation step schema
export const CalculationStepSchema = z.object({
  stepId: z.string(),
  description: z.string(),
  operation: z.enum(['ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'AVERAGE', 'LOOKUP', 'FILTER', 'GROUP', 'MATCH']),
  inputIds: z.array(z.string()),
  outputId: z.string(),
  order: z.number().int(),
})

// Confidence schema
export const ConfidenceSchema = z.object({
  value: z.number().int().min(0).max(10000),
  reason: z.string().optional(),
})

// Explanation schema
export const ExplanationSchema = z.object({
  metric: z.string(),
  value: z.number().int(),
  confidence: ConfidenceSchema,
  evidence: z.array(EvidenceSchema),
  sources: z.array(SourceReferenceSchema),
  calculationSteps: z.array(CalculationStepSchema),
})

// Type exports
export type SourceReferenceDto = z.infer<typeof SourceReferenceSchema>
export type EvidenceDto = z.infer<typeof EvidenceSchema>
export type CalculationStepDto = z.infer<typeof CalculationStepSchema>
export type ConfidenceDto = z.infer<typeof ConfidenceSchema>
export type ExplanationDto = z.infer<typeof ExplanationSchema>