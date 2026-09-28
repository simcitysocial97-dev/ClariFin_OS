import { http, HttpResponse } from 'msw'

export const bankHandlers = [
  http.get('/api/v1/banks', () => {
    return HttpResponse.json({
      banks: ['HDFC', 'SBI', 'ICICI'],
    })
  }),
]