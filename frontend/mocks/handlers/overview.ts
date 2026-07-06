import { http, HttpResponse } from 'msw'
import { mockOverview } from '../fixtures/overview'

export const overviewHandlers = [
  http.get('/api/overview', () => {
    return HttpResponse.json(mockOverview)
  }),
]