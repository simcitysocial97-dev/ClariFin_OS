import { z } from 'zod'
import type { InvestmentType } from '@/types/investments-view-model'

export type { InvestmentType } from '@/types/investments-view-model'

/**
 * Investments API contract.
 *
 * `investment_type` mirrors the backend's canonical `InvestmentType` Literal
 * (`backend/src/core/dtos/investments_dto.py`). M11 found the write path
 * accepted a free-form string while the read path demanded this closed enum, so
 * any value outside it was stored and then broke `GET /api/v1/investments`.
 * Both ends now speak the same vocabulary, and the form offers only these.
 */
export const INVESTMENT_TYPES = [
  'stocks',
  'mutual_funds',
  'bonds',
  'fd',
  'ppf',
  'gold',
  'other',
] as const satisfies readonly InvestmentType[]

export const InvestmentTypeSchema = z.enum(INVESTMENT_TYPES)

export const InvestmentSummarySchema = z.object({
  // M11: the backend coerces the primary key to a string on both the mutation
  // response and the portfolio read. It was `z.union([z.string(), z.number()])`
  // to tolerate a disagreement between the two; they now agree.
  id: z.string(),
  name: z.string(),
  type: InvestmentTypeSchema,
  institution: z.string(),
  current_value_paise: z.number().int(),
  invested_paise: z.number().int(),
  returns_paise: z.number().int(),
  returns_percentage: z.number(),
  returns_ytd_bps: z.number().int(),
  status: z.enum(['active', 'closed', 'matured']),
})

export const InvestmentsResponseSchema = z.object({
  investments: z.array(InvestmentSummarySchema),
  total_value_paise: z.number().int(),
  total_invested_paise: z.number().int(),
  total_returns_paise: z.number().int(),
  investment_count: z.number().int().nonnegative(),
  insights: z.array(z.record(z.string(), z.unknown())),
  evidence_chain: z.unknown().nullable(),
})

export type InvestmentsResponse = z.infer<typeof InvestmentsResponseSchema>
export type InvestmentSummary = z.infer<typeof InvestmentSummarySchema>