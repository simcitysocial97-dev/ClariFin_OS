/**
 * API response schemas must accept what the authority actually emits.
 *
 * M10-A3. These are regression tests for three real defects, each of which put
 * a visible "Unable to load data / Try again" band on /dashboard or a wrong
 * number on /behaviour while the backend answered HTTP 200:
 *
 *  1. `GET /api/v1/overview` emits `"statement_period_from": null` /
 *     `"statement_period_to": null` for every imported transaction without a
 *     statement period. The schema typed them `z.string().optional()`, which
 *     accepts `undefined` but not `null` -> 2 issues per row, whole payload
 *     rejected.
 *  2. `GET /api/v1/analytics` emits `avg_monthly: 9974.17` and a per-month
 *     `average: 9974.17`. A rupee average is fractional by construction, but the
 *     schema declared both `z.number().int()` -> 7 issues, payload rejected.
 *  3. `GET /api/v1/behaviour/wellness-score` returns `score: "100"` with band
 *     `"Excellent"`. The authority's scale is 0-100
 *     (backend/src/models/behaviour.py:31, engines/behaviour_engine/wellness.py:83),
 *     but the schema validated against a basis-point 0-10000 range.
 *
 * The fixtures below are trimmed copies of real responses captured from a
 * running backend, not invented shapes.
 */

import { describe, it, expect } from 'vitest';
import { OverviewSchema } from '@/lib/schemas/overview';
import { AnalyticsSchema } from '@/lib/schemas/analytics';
import { BehaviorScoreSchema } from '@/lib/schemas/behavior-score';

describe('OverviewSchema — nullable statement periods', () => {
  const base = {
    total_spend: 59845.0,
    total_spend_display: '₹59,845.00',
    this_month: 9779.0,
    this_month_display: '₹9,779.00',
    last_month: 10540.0,
    last_month_display: '₹10,540.00',
    month_change: '-7.2%',
    transaction_count: 17,
    card_count: 1,
    months_of_data: 6,
    monthly_average: 9974.166666666666,
    monthly_average_display: '₹9,974.17',
    above_below_avg: '₹195.17 below avg',
    above_avg_is_bad: false,
    monthly_chart: [{ month: 'Jan 26', amount: 9299.0 }],
    category_chart: [{ name: 'Shopping', value: 26798.0 }],
    behavioral_insights: [],
  };

  it('accepts the null statement period fields the API emits', () => {
    const result = OverviewSchema.safeParse({
      ...base,
      recent_transactions: [
        {
          id: 29,
          date: '19/06/2026',
          description: 'Uber Trip',
          amount_paise: 78000,
          type: 'debit',
          category: 'Travel',
          subcategory: 'Cabs',
          raw_description: null,
          member: 'Self',
          bank: 'Manual Import',
          statement_file: 'seed.csv',
          statement_period_from: null,
          statement_period_to: null,
        },
      ],
    });

    expect(result.success).toBe(true);
  });

  it('still accepts a populated statement period', () => {
    const result = OverviewSchema.safeParse({
      ...base,
      recent_transactions: [
        {
          id: 1,
          date: '05/01/2026',
          description: 'Salary Credit',
          type: 'credit',
          category: 'salary',
          member: 'Self',
          bank: 'HDFC Bank',
          statement_period_from: '2026-01-01',
          statement_period_to: '2026-01-31',
        },
      ],
    });

    expect(result.success).toBe(true);
  });
});

describe('AnalyticsSchema — rupee averages are not integers', () => {
  const payload = {
    highest_month: 'Apr 26',
    highest_month_amount: '₹14,839.00',
    avg_monthly: 9974.17,
    avg_monthly_display: '₹9,974.17',
    biggest_transaction: {
      description: 'Amazon Purchase',
      amount: 11200.0,
      date: '16/04/2026',
      bank: 'Manual Import',
    },
    unique_merchants: 11,
    spending_trend: [
      { month: 'Jan 26', amount: 9299.0, average: 9974.17 },
      { month: 'Apr 26', amount: 14839.0, average: 9974.17 },
    ],
    day_of_week: [
      { day: 'Mon', amount: 7060.0, count: 4 },
      { day: 'Thu', amount: 24500.0, count: 4 },
    ],
    top_merchants: [{ merchant: 'Amazon Purchase', amount_display: '₹17,799.00', count: 2 }],
    recurring_charges: [
      {
        description: 'Netflix Subscription',
        frequency: 2,
        avg_display: '₹649.00',
        annual_display: '₹7,788.00',
      },
    ],
    largest_transactions: [
      {
        rank: 1,
        date_display: '16 Apr 2026',
        description: 'Amazon Purchase',
        amount_display: '₹11,200.00',
        bank: 'Manual Import',
      },
    ],
  };

  it('accepts a fractional avg_monthly and per-point average', () => {
    expect(AnalyticsSchema.safeParse(payload).success).toBe(true);
  });

  it('still rejects a non-numeric avg_monthly', () => {
    const result = AnalyticsSchema.safeParse({ ...payload, avg_monthly: 'not-a-number' });
    expect(result.success).toBe(false);
  });
});

describe('BehaviorScoreSchema — accepts the value the backend actually emits', () => {
  const payload = {
    score: '100',
    band: 'Excellent',
    components: {
      cashflow_health: '100',
      debt_health: '1',
      savings_behaviour: '100',
      resilience: '100',
      lifestyle_control: '100',
      credit_behaviour: '0.5',
    },
    snapshot_date: '2026-10-02',
    version: 1,
  };

  it('accepts the string-encoded Decimal the API emits', () => {
    const result = BehaviorScoreSchema.safeParse(payload);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.score).toBe(100);
      expect(result.data.components.debt_health).toBe(1);
    }
  });

  it('rejects a negative value', () => {
    // A basis-point magnitude is NOT rejected here, because the backend does
    // not currently honour its own 0-100 contract: `get_wellness_score` returns
    // the raw stored `snapshot["wellness_score"]`, and the live value is
    // 7561.45. M10-A3 asserted a 0-100 bound on the strength of the model
    // docstring, which is right about the contract and wrong about the
    // implementation; enforcing it turned the whole /behaviour page into an
    // error state. The scale defect belongs to the backend. This assertion is
    // kept because a negative score is still rejected under either reading.
    expect(BehaviorScoreSchema.safeParse({ ...payload, score: '-1' }).success).toBe(false);
  });

  it('accepts the value the backend actually emits today', () => {
    // Regression guard for the above: while the backend returns a
    // double-scaled snapshot value, the schema must not reject it, or
    // /behaviour renders an error state instead of the score.
    const result = BehaviorScoreSchema.safeParse({ ...payload, score: '7561.45' });
    expect(result.success).toBe(true);
  });
});
