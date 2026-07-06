import { http, HttpResponse } from 'msw'

export const categoryHandlers = [
  http.get('/api/categories/list', () => {
    return HttpResponse.json({
      categories: ['Food & Dining', 'Transport', 'Income', 'Shopping', 'Utilities'],
    })
  }),
]