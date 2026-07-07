import { http, HttpResponse } from 'msw'
import { mockBehaviorScore, mockBehaviorInsights } from '../fixtures/behavior'

export const behaviorHandlers = [
  http.get('/api/behavior/score', () => {
    return HttpResponse.json(mockBehaviorScore)
  }),
  http.get('/api/behavior/insights', () => {
    return HttpResponse.json(mockBehaviorInsights)
  }),
]