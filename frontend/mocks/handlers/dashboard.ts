import { http, HttpResponse } from 'msw'
import { mockDashboardSummary } from '../fixtures/dashboard'

export const dashboardHandlers = [
  http.get('/api/dashboard/summary', () => {
    return HttpResponse.json(mockDashboardSummary)
  }),
]