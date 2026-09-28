// WellnessScoreResponse shape — aligns with /api/v1/behaviour/wellness-score
export const mockBehaviorScore = {
  score: 72,
  band: 'Healthy' as const,
  components: {
    cashflow_health: 80,
    debt_health: 90,
    savings_behaviour: 75,
    resilience: 68,
    lifestyle_control: 85,
    credit_behaviour: 70,
  },
  snapshot_date: '2025-01-15',
  version: 1,
  // Legacy optional fields (backward compat with older consumers)
  financial_health_score: 72,
  risk_flags: {
    high_impulsivity: false,
    high_stress: false,
    low_savings: false,
  } as Record<string, boolean>,
  summary: 'Your financial health is good.',
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
