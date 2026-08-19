import { http, HttpResponse } from 'msw'

const mockReconciliationsResponse = {
  reconciliations: [
    {
      id: 1,
      debit_txn_id: 101,
      credit_txn_id: 201,
      debit_account_id: 'HDFC Bank',
      credit_account_id: 'ICICI Bank',
      amount: 45000.0,
      date_diff_days: 1,
      match_confidence: 0.7,
      match_type: 'window',
      status: 'pending',
      created_at: '2025-01-15T10:00:00',
      confirmed_at: null,
      debit_date: '15/01/2025',
      debit_date_iso: '2025-01-15',
      debit_description: 'CC PAYMENT',
      debit_amount_paise: 4500000,
      debit_bank: 'HDFC Bank',
      credit_date: '16/01/2025',
      credit_date_iso: '2025-01-16',
      credit_description: 'SALARY CREDIT',
      credit_amount_paise: 4500000,
      credit_bank: 'ICICI Bank',
    },
    {
      id: 2,
      debit_txn_id: 102,
      credit_txn_id: 202,
      debit_account_id: 'SBI',
      credit_account_id: 'HDFC Bank',
      amount: 12000.0,
      date_diff_days: 0,
      match_confidence: 0.8,
      match_type: 'exact',
      status: 'pending',
      created_at: '2025-01-14T10:00:00',
      confirmed_at: null,
      debit_date: '14/01/2025',
      debit_date_iso: '2025-01-14',
      debit_description: 'UPI TRANSFER',
      debit_amount_paise: 1200000,
      debit_bank: 'SBI',
      credit_date: '14/01/2025',
      credit_date_iso: '2025-01-14',
      credit_description: 'UPI RECEIVED',
      credit_amount_paise: 1200000,
      credit_bank: 'HDFC Bank',
    },
  ],
}

const mockScanResponse = {
  matches: [
    {
      debit_txn_id: 101,
      credit_txn_id: 201,
      debit_account_id: 'HDFC Bank',
      credit_account_id: 'ICICI Bank',
      amount: 45000.0,
      date_diff_days: 1,
      match_confidence: 0.7,
      match_type: 'window',
      deterministic_key: '101:201',
      explanation: 'Window match: ₹45000.00 transferred from HDFC Bank (2025-01-15) to ICICI Bank (2025-01-16), 1 days apart',
    },
  ],
  count: 1,
}

export const reconciliationHandlers = [
  http.get('/api/reconciliation', () => {
    return HttpResponse.json(mockReconciliationsResponse)
  }),

  http.get('/api/reconciliation/pending', () => {
    return HttpResponse.json(mockReconciliationsResponse)
  }),

  http.get('/api/reconciliation/scan', () => {
    return HttpResponse.json(mockScanResponse)
  }),

  http.post('/api/reconciliation/:id/confirm', () => {
    return HttpResponse.json({ success: true, status: 'confirmed' })
  }),

  http.post('/api/reconciliation/:id/reject', () => {
    return HttpResponse.json({ success: true, status: 'rejected' })
  }),
]