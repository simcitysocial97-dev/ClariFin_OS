import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

const AccountSchema = z.object({
  id: z.string(),
  name: z.string(),
  bank: z.string(),
  account_type: z.string(),
  balance_paise: z.number().int(),
  account_number_last4: z.string().nullable(),
  is_active: z.number(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

const AccountsResponseSchema = z.object({
  accounts: z.array(AccountSchema),
  total: z.number().int(),
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

async function fetchManagedAccounts() {
  const res = await fetch(`${API_BASE}/api/accounts/manage`)
  if (!res.ok) throw new Error('Failed to fetch accounts')
  const raw = await res.json()
  return AccountsResponseSchema.parse(raw)
}

async function createAccount(input: CreateAccountInput) {
  const res = await fetch(`${API_BASE}/api/accounts/manage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to create account')
  return res.json()
}

async function updateAccount(id: string, input: Partial<CreateAccountInput>) {
  const res = await fetch(`${API_BASE}/api/accounts/manage/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to update account')
  return res.json()
}

async function deleteAccount(id: string) {
  const res = await fetch(`${API_BASE}/api/accounts/manage/${id}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error('Failed to delete account')
  return res.json()
}

export function useManagedAccounts() {
  return useQuery({
    queryKey: ['accounts', 'managed'],
    queryFn: fetchManagedAccounts,
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