import { http, HttpResponse } from 'msw'
import { mockTransactionList } from '../fixtures/transactions'

export const transactionHandlers = [
  http.get('/api/transactions', ({ request }) => {
    const url = new URL(request.url)
    const search = url.searchParams.get('search')
    const bank = url.searchParams.get('bank')
    const category = url.searchParams.get('category')
    const type = url.searchParams.get('type')
    
    let filtered = mockTransactionList
    
    if (search) {
      filtered = filtered.filter(t => 
        t.description.toLowerCase().includes(search.toLowerCase())
      )
    }
    if (bank && bank !== 'All') {
      filtered = filtered.filter(t => t.bank === bank)
    }
    if (category && category !== 'All') {
      filtered = filtered.filter(t => t.category === category)
    }
    if (type && type !== 'All') {
      filtered = filtered.filter(t => t.type === type)
    }
    
    return HttpResponse.json({
      transactions: filtered,
      total: filtered.length,
    })
  }),
]