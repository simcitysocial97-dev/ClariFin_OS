/**
 * NetWorth API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 * SourceReference schema mirrors backend model exactly.
 */

import { z } from 'zod'

// Source reference schema - mirrors backend SourceReference
const SourceReferenceSchema = z.object({
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
const EvidenceSchema = z.object({
  id: z.string(),
  type: z.enum(['data', 'calculation', 'source']),
  description: z.string(),
  value: z.union([z.number(), z.string(), z.boolean()]).nullable(),
  sourceId: z.union([z.string(), z.number()]).optional(),
})

// Calculation step schema
const CalculationStepSchema = z.object({
  stepId: z.string(),
  description: z.string(),
  operation: z.enum(['ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'AVERAGE', 'LOOKUP', 'FILTER', 'GROUP', 'MATCH']),
  inputIds: z.array(z.string()),
  outputId: z.string(),
  order: z.number().int(),
})

// Confidence schema
const ConfidenceSchema = z.object({
  value: z.number().int().min(0).max(10000),
  reason: z.string().optional(),
})

// Explanation schema
const ExplanationSchema = z.object({
  metric: z.string(),
  value: z.number().int(),
  confidence: ConfidenceSchema,
  evidence: z.array(EvidenceSchema),
  sources: z.array(SourceReferenceSchema),
  calculationSteps: z.array(CalculationStepSchema),
})

// NetWorth explanation schema
const NetWorthExplanationSchema = z.object({
  netWorth: ExplanationSchema,
  assets: ExplanationSchema,
  liabilities: ExplanationSchema,
  confidenceReason: z.string().optional(),
})

/**
 * NetWorth response from /api/networth
 */
export const NetWorthResponseSchema = z.object({
  net_worth_paise: z.number().int(),
  assets: z.object({
    total_paise: z.number().int(),
    accounts_paise: z.number().int(),
    investments_paise: z.number().int(),
    account_count: z.number().int(),
    investment_count: z.number().int(),
  }),
  liabilities: z.object({
    total_paise: z.number().int(),
    loans_paise: z.number().int(),
    cards_paise: z.number().int(),
    loan_count: z.number().int(),
    card_count: z.number().int(),
  }),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: NetWorthExplanationSchema.optional(),
})

export type NetWorthDto = z.infer<typeof NetWorthResponseSchema>
export type { SourceReferenceSchema, EvidenceSchema, CalculationStepSchema, ConfidenceSchema, ExplanationSchema, NetWorthExplanationSchema }