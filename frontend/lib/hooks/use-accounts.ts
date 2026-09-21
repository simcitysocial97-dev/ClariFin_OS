import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api/gateway';
import { z } from 'zod'

// Canonical account schema matching /api/v1/accounts AccountDetailDTO
const AccountSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['savings', 'current', 'credit_card', 'investment', 'loan', 'other']),
  institution: z.string(),
  balance_paise: z.number().int(),
  currency: z.string().default('INR'),
  status: z.enum(['active', 'inactive', 'closed']),
  account_number_last4: z.string().nullable(),
  opened_date: z.string().nullable(),
  closed_date: z.string().nullable(),
  notes: z.string().nullable(),
})


export type Account = z.infer<typeof AccountSchema>

export interface CreateAccountInput {
  name: string
  bank: string
  account_type: string
  balance_paise: number
  account_number_last4?: string
  notes?: string
}

async function fetchAccounts(): Promise<{ accounts: Account[]; total: number }> {
  const res = await apiFetch(`/api/v1/accounts`)
  if (!res.ok) throw new Error('Failed to fetch accounts')
  const raw = await res.json()
  // V1 returns plain array — wrap to match legacy consumer contract
  const parsed = z.array(AccountSchema).safeParse(raw)
  if (!parsed.success) {
    console.error('❌ Accounts API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  return { accounts: parsed.data, total: parsed.data.length }
}

async function createAccount(input: CreateAccountInput) {
  const res = await apiFetch(`/api/v1/accounts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: input.name,
      bank: input.bank,
      account_type: input.account_type,
      balance_paise: input.balance_paise,
      account_number_last4: input.account_number_last4 ?? null,
      notes: input.notes ?? null,
    }),
  })
  if (!res.ok) throw new Error('Failed to create account')
  return res.json()
}

async function updateAccount(id: string, input: Partial<CreateAccountInput>) {
  const res = await apiFetch(`/api/v1/accounts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...(input.name !== undefined && { name: input.name }),
      ...(input.bank !== undefined && { bank: input.bank }),
      ...(input.account_type !== undefined && { account_type: input.account_type }),
      ...(input.balance_paise !== undefined && { balance_paise: input.balance_paise }),
      ...(input.account_number_last4 !== undefined && { account_number_last4: input.account_number_last4 }),
      ...(input.notes !== undefined && { notes: input.notes }),
    }),
  })
  if (!res.ok) throw new Error('Failed to update account')
  return res.json()
}

async function deleteAccount(id: string) {
  const res = await apiFetch(`/api/v1/accounts/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to deactivate account')
  return res.json()
}

export function useManagedAccounts() {
  return useQuery({
    queryKey: ['accounts', 'v1'],
    queryFn: fetchAccounts,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCreateAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export function useUpdateAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & Partial<CreateAccountInput>) =>
      updateAccount(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export function useDeleteAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}
