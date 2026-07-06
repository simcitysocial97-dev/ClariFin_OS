import { http, HttpResponse } from 'msw'

export const cashflowHandlers = [
  http.get('/api/cashflow/monthly', () => {
    return HttpResponse.json({
      months: [
        {
          month_key: '2024-08',
          month_label: 'Aug 2024',
          income_paise: 450000,
          expense_paise: 380000,
          net_paise: 70000,
          transaction_count: 42,
        },
        {
          month_key: '2024-09',
          month_label: 'Sep 2024',
          income_paise: 480000,
          expense_paise: 410000,
          net_paise: 70000,
          transaction_count: 38,
        },
        {
          month_key: '2024-10',
          month_label: 'Oct 2024',
          income_paise: 520000,
          expense_paise: 450000,
          net_paise: 70000,
          transaction_count: 45,
        },
        {
          month_key: '2024-11',
          month_label: 'Nov 2024',
          income_paise: 490000,
          expense_paise: 420000,
          net_paise: 70000,
          transaction_count: 40,
        },
        {
          month_key: '2024-12',
          month_label: 'Dec 2024',
          income_paise: 550000,
          expense_paise: 480000,
          net_paise: 70000,
          transaction_count: 48,
        },
        {
          month_key: '2025-01',
          month_label: 'Jan 2025',
          income_paise: 510000,
          expense_paise: 430000,
          net_paise: 80000,
          transaction_count: 44,
        },
      ],
      period_months: 6,
      total_income_paise: 2900000,
      total_expense_paise: 2550000,
      total_net_paise: 350000,
    })
  }),
]