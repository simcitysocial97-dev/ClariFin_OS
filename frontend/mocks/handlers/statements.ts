import { http, HttpResponse } from 'msw'
import { mockStatementList } from '../fixtures/statements'

export const statementHandlers = [
  http.get('/api/statements', () => {
    return HttpResponse.json(mockStatementList)
  }),
]