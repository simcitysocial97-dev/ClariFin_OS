import { transactionHandlers } from './transactions'
import { overviewHandlers } from './overview'
import { statementHandlers } from './statements'
import { bankHandlers } from './banks'
import { categoryHandlers } from './categories'
import { dashboardHandlers } from './dashboard'
import { cashflowHandlers } from './cashflow'
import { accountHandlers } from './accounts'
import { behaviorHandlers } from './behavior'
import { analyticsHandlers } from './analytics'
import { cardHandlers } from './cards'
import { reconciliationHandlers } from './reconciliation'

export const handlers = [
  ...transactionHandlers,
  ...overviewHandlers,
  ...statementHandlers,
  ...bankHandlers,
  ...categoryHandlers,
  ...dashboardHandlers,
  ...cashflowHandlers,
  ...accountHandlers,
  ...behaviorHandlers,
  ...analyticsHandlers,
  ...cardHandlers,
  ...reconciliationHandlers,
]