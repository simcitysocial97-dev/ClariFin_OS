import { http, HttpResponse } from 'msw'
import { mockAnalytics } from '../fixtures/analytics'

export const analyticsHandlers = [
  http.get('/api/v1/analytics', () => {
    return HttpResponse.json(mockAnalytics)
  }),
]