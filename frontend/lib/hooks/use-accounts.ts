import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api/gateway';
import { z } from 'zod'


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
  const res = await apiFetch(`/api/accounts/manage`)
  if (!res.ok) throw new Error('Failed to fetch accounts')
  
  // This is unverified raw payload from the network
  const raw = await res.json()
  
  // Intercept and parse data before passing it to frontend state loaders
  const parsed = AccountsResponseSchema.safeParse(raw)
  
  if (!parsed.success) {
    // Safely prints exact path anomalies and mismatched value types to the browser console
    console.error('❌ Accounts API response validation failed:', parsed.error.issues)
    throw new Error('API response shape mismatch — check backend contract')
  }
  
  return parsed.data
}

async function createAccount(input: CreateAccountInput) {
  const res = await apiFetch(`/api/accounts/manage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to create account')
  return res.json()
}

async function updateAccount(id: string, input: Partial<CreateAccountInput>) {
  const res = await apiFetch(`/api/accounts/manage/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error('Failed to update account')
  return res.json()
}

async function deleteAccount(id: string) {
  const res = await apiFetch(`/api/accounts/manage/${id}`, {
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