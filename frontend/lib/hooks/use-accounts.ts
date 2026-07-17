/**
 * Accounts Hook - Compatibility layer
 *
 * Re-exports migrated useManagedAccounts from capability module.
 * Mutation hooks (create/update/delete) remain here until migrated.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'

// Re-export migrated hook and type from capability
export { useManagedAccounts } from '@/lib/capabilities/accounts'
export type { AccountModel as Account } from '@/lib/capabilities/accounts'

// ============================================================
// Mutation hooks (not yet migrated)
// ============================================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

export interface CreateAccountInput {
  name: string
  bank: string
  account_type: string
  balance_paise: number
  account_number_last4?: string
  notes?: string
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