/**
 * Widget Registry - Single source of truth for all dashboard widgets
 * 
 * Allows for centralized widget management and future dynamic loading.
 */

import { FinancialHealthHero } from './financial-health-hero';
import { FinancialInboxWidget } from './financial-inbox-widget';
import { MoneyPositionWidget } from './money-position-widget';
import { BorrowingWidget } from './borrowing-widget';
import { SpendingWidget } from './spending/SpendingWidget';
import { MerchantWidget } from './spending/MerchantWidget';

export const dashboardWidgets = [
  { name: 'FinancialHealthHero', component: FinancialHealthHero },
  { name: 'FinancialInboxWidget', component: FinancialInboxWidget },
  { name: 'MoneyPositionWidget', component: MoneyPositionWidget },
  { name: 'BorrowingWidget', component: BorrowingWidget },
  { name: 'SpendingWidget', component: SpendingWidget },
  { name: 'MerchantWidget', component: MerchantWidget },
] as const;

export type DashboardWidgetName = (typeof dashboardWidgets)[number]['name'];