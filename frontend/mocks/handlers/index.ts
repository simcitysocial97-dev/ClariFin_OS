import { transactionHandlers } from './transactions'
import { overviewHandlers } from './overview'
import { statementHandlers } from './statements'
import { bankHandlers } from './banks'
import { categoryHandlers } from './categories'
import { dashboardHandlers } from './dashboard'
import { cashflowHandlers } from './cashflow'
import { accountHandlers } from './accounts'

export const handlers = [
  ...transactionHandlers,
  ...overviewHandlers,
  ...statementHandlers,
  ...bankHandlers,
  ...categoryHandlers,
  ...dashboardHandlers,
  ...cashflowHandlers,
  ...accountHandlers,
]
