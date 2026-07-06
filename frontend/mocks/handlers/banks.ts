import { http, HttpResponse } from 'msw'

export const bankHandlers = [
  http.get('/api/banks', () => {
    return HttpResponse.json({
      banks: ['HDFC', 'SBI', 'ICICI'],
    })
  }),
]