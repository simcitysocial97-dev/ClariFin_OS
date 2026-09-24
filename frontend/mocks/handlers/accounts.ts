import { http, HttpResponse } from 'msw'
import { mockAccounts } from '../fixtures/accounts'

let accounts = [...mockAccounts]
let accountIdCounter = 2

export const accountHandlers = [
  // GET /api/v1/accounts - Get all accounts
  http.get('/api/v1/accounts', () => {
    return HttpResponse.json({ accounts })
  }),

  // POST /api/v1/accounts - Create account
  http.post('/api/v1/accounts', async ({ request }) => {
    const body = await request.json() as any
    const newAccount = {
      id: String(accountIdCounter++),
      name: body.name,
      bank_name: body.bank_name,
      account_type: body.account_type || 'Savings',
      balance_paise: Math.round(body.balance * 100), // Convert rupees to paise
      last_updated: new Date().toISOString(),
    }
    accounts.push(newAccount)
    return HttpResponse.json(newAccount)
  }),

  // PUT /api/v1/accounts/{id} - Update account
  http.put('/api/v1/accounts/:id', async ({ request, params }) => {
    const id = params.id as string
    const body = await request.json() as any
    
    const index = accounts.findIndex(a => a.id === id)
    if (index === -1) {
      return new HttpResponse(null, { status: 404 })
    }
    
    accounts[index] = {
      ...accounts[index],
      ...body,
      balance_paise: body.balance !== undefined ? Math.round(body.balance * 100) : accounts[index].balance_paise,
      last_updated: new Date().toISOString(),
    }
    
    return HttpResponse.json(accounts[index])
  }),

  // DELETE /api/v1/accounts/{id} - Delete account
  http.delete('/api/v1/accounts/:id', ({ params }) => {
    const id = params.id as string
    const index = accounts.findIndex(a => a.id === id)
    if (index === -1) {
      return new HttpResponse(null, { status: 404 })
    }
    accounts = accounts.filter(a => a.id !== id)
    return HttpResponse.json({ success: true, message: 'Account deleted' })
  }),
]