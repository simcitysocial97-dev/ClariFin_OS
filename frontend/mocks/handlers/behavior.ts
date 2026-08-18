import { http, HttpResponse } from 'msw'
import { mockBehaviorScore, mockBehaviorInsights } from '../fixtures/behavior'

export const behaviorHandlers = [
  http.get('/api/v1/behaviour/wellness-score', () => {
    return HttpResponse.json(mockBehaviorScore)
  }),
]
