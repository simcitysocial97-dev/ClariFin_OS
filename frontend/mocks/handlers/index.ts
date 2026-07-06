import { transactionHandlers } from './transactions'
import { overviewHandlers } from './overview'
import { statementHandlers } from './statements'
import { bankHandlers } from './banks'
import { categoryHandlers } from './categories'
import { dashboardHandlers } from './dashboard'

export const handlers = [
  ...transactionHandlers,
  ...overviewHandlers,
  ...statementHandlers,
  ...bankHandlers,
  ...categoryHandlers,
  ...dashboardHandlers,
]