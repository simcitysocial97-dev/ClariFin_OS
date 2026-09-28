import { http, HttpResponse } from 'msw'

export const categoryHandlers = [
  http.get('/api/v1/categories/list', () => {
    return HttpResponse.json({
      categories: ['Food & Dining', 'Transport', 'Income', 'Shopping', 'Utilities'],
    })
  }),
]