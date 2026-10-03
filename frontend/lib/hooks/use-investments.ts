import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, ApiError, ApiTimeoutError } from '@/lib/api/gateway';
import {
  InvestmentsResponseSchema,
  InvestmentTypeSchema,
  type InvestmentSummary,
  type InvestmentType,
} from '@/lib/schemas/investments'


const INVESTMENTS_QUERY_KEY = 'investments'


export type Investment = InvestmentSummary

export interface CreateInvestmentInput {
  name: string
  investment_type: InvestmentType
  invested_paise: number
  current_value_paise: number
  as_of_date: string
  units?: number
  buy_price_paise?: number
  current_price_paise?: number
  notes?: string
}

async function fetchInvestments() {
  const res = await apiFetch(`/api/v1/investments`)
  if (!res.ok) throw new Error('Failed to fetch investments')

  // This is unverified raw payload from the network
  const raw = await res.json()

  // Intercept and parse data before passing it to frontend state loaders
  const parsed = InvestmentsResponseSchema.safeParse(raw)

  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Investments API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }

  return parsed.data
}

/**
 * Surface the authority's own rejection rather than a generic message.
 *
 * M11: `createInvestment` threw the constant 'Failed to create investment' for
 * every outcome, which is why `POST /api/v1/investments` returning HTTP 500 for
 * four stacked backend defects was invisible to the user — the hook reported the
 * same string it reports for a network drop.
 *
 * `apiFetch` throws `ApiError` on a non-OK response (carrying the raw payload on
 * `body`) and `ApiTimeoutError` on a deadline, so the reason is read out of
 * whichever it produced. A 422 naming the offending field is therefore shown to
 * the user instead of the bare `API 422 /api/v1/investments`.
 */
function describeFailure(cause: unknown, fallback: string): Error {
  if (cause instanceof ApiTimeoutError) {
    return new Error(`${fallback}: the request timed out (${cause.message})`)
  }
  if (cause instanceof ApiError) {
    const detail = extractDetail(cause.body)
    return new Error(
      detail ? `${fallback}: ${detail}` : `${fallback} (HTTP ${cause.status})`
    )
  }
  if (cause instanceof Error) return cause
  return new Error(fallback)
}

/** Pull a human-readable reason out of a FastAPI error payload. */
function extractDetail(rawBody: string): string | null {
  if (!rawBody) return null
  try {
    const body = JSON.parse(rawBody)
    if (typeof body?.detail === 'string' && body.detail.trim() !== '') {
      return body.detail
    }
    if (Array.isArray(body?.detail) && body.detail.length > 0) {
      const messages = body.detail
        .map((entry: { loc?: unknown[]; msg?: string }) =>
          `${entry.loc ? `${entry.loc.join('.')}: ` : ''}${entry.msg ?? ''}`
        )
        .filter((message: string) => message.trim() !== '')
      if (messages.length > 0) return messages.join('; ')
    }
    if (typeof body?.error?.message === 'string' && body.error.message.trim() !== '') {
      return body.error.message
    }
    if (typeof body?.message === 'string' && body.message.trim() !== '') {
      return body.message
    }
  } catch {
    // A non-JSON body (a proxy error page, an HTML 502) carries no structured
    // reason; the status alone is reported rather than a parse failure.
  }
  return null
}

/** Run a request, translating any transport or status failure into a message. */
async function withReportedFailure<T>(run: () => Promise<T>, fallback: string): Promise<T> {
  try {
    return await run()
  } catch (cause) {
    throw describeFailure(cause, fallback)
  }
}

async function createInvestment(input: CreateInvestmentInput) {
  return withReportedFailure(async () => {
    const res = await apiFetch(`/api/v1/investments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    })
    // `apiFetch` throws on a non-OK response; this branch only runs if that
    // contract changes, and it must not silently drop the reason.
    if (!res.ok) {
      const detail = extractDetail(await res.text())
      throw new Error(detail ?? `HTTP ${res.status}`)
    }
    return res.json()
  }, 'Failed to create investment')
}

async function updateInvestment(id: string, input: Partial<CreateInvestmentInput>) {
  return withReportedFailure(async () => {
    const res = await apiFetch(`/api/v1/investments/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    })
    if (!res.ok) {
      const detail = extractDetail(await res.text())
      throw new Error(detail ?? `HTTP ${res.status}`)
    }
    return res.json()
  }, 'Failed to update investment')
}

async function deleteInvestment(id: string) {
  return withReportedFailure(async () => {
    const res = await apiFetch(`/api/v1/investments/${id}`, { method: 'DELETE' })
    if (!res.ok) {
      const detail = extractDetail(await res.text())
      throw new Error(detail ?? `HTTP ${res.status}`)
    }
    return res.json()
  }, 'Failed to delete investment')
}

export function useInvestments() {
  return useQuery({
    queryKey: [INVESTMENTS_QUERY_KEY],
    queryFn: fetchInvestments,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * `onSuccess` invalidates the prefix `['investments']`, which React Query
 * prefix-matches — so it also invalidates the workspace query
 * `['investments', queryParams]` that `useInvestmentsCapability` reads
 * `/api/v1/workspaces/investments` through. That is the path by which a created
 * holding reaches the rendered table.
 */
export function useCreateInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createInvestment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [INVESTMENTS_QUERY_KEY] }),
  })
}

export function useUpdateInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & Partial<CreateInvestmentInput>) =>
      updateInvestment(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [INVESTMENTS_QUERY_KEY] }),
  })
}

export function useDeleteInvestment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteInvestment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [INVESTMENTS_QUERY_KEY] }),
  })
}

/** Re-exported so the vocabulary has one definition in the frontend. */
export { InvestmentTypeSchema }