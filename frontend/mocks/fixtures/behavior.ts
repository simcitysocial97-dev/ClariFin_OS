export const mockBehaviorScore = {
  financial_health_score: 72,
  confidence: 0.85,
  components: {
    savings_discipline: 0.75,
    habit_stability: 0.68,
    impulsivity: 0.35,
    financial_stress: 0.25,
    loss_aversion: 0.42,
  },
  risk_flags: {
    india_specific: {
      upi_micro_spend_flag: false,
      gambling_flag: false,
      loan_app_pattern_flag: false,
      loan_credit_count: 0,
      emi_ratio: 0.22,
      monthly_emi_total: 15000,
    },
    high_impulsivity: false,
    high_stress: false,
    low_savings: false,
  },
  summary: 'Your financial behavior shows strong discipline with savings discipline being strong and spending is well-controlled.',
};

export const mockBehaviorInsights = {
  insights: [
    {
      type: 'warning',
      title: 'Spending Trending Up',
      message: 'Spending trend is up 15% over the past week. Monitor for sustained increases.',
      metric: 'trend',
      value: 0.15,
    },
    {
      type: 'positive',
      title: 'Strong Savings Rate',
      message: 'Saving 22% of income monthly. This exceeds the recommended 20% target.',
      metric: 'savings_rate',
      value: 0.22,
    },
    {
      type: 'positive',
      title: 'Consistent Spending Habits',
      message: 'Category spending is highly stable (CV: 12%). This indicates strong financial discipline.',
      metric: 'category_cv',
      value: 0.12,
    },
  ],
  nudges: [],
  top_nudge: null,
  summary: 'Your financial behavior shows strong discipline.',
  financial_health_score: 72,
  confidence: 0.85,
};