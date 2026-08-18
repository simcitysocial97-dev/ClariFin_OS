export const mockDashboardSummary = {
  net_cash_flow_paise: 5000000, // ₹50,000.00 in paise
  net_cash_flow_rupees: null, // DEPRECATED — always null post Phase 2
  total_income_paise: 10000000, // ₹1,00,000.00
  total_expenses_paise: 7500000, // ₹75,000.00
  savings_rate: 25.0, // percentage (0-100) per DTO spec
  emi_paise: 1250000, // ₹12,500.00
  emi_ratio: 12.5, // percentage (0-100) per DTO spec
  buffer_days: 45,
  financial_health_score: 75,
  seven_day_trend: 0.05,
  category_drift_alert: null,
  recent_transactions: [],
}
