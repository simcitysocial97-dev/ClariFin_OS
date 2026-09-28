import { http, HttpResponse } from 'msw'
import { mockStatementList } from '../fixtures/statements'

export const statementHandlers = [
  http.get('/api/v1/statements', () => {
    return HttpResponse.json(mockStatementList)
  }),
]