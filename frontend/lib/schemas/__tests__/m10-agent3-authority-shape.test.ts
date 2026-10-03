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
 *     `"Excellent"` for the no-data fallback, but `score: "7561.45"` against
 *     real data — the backend double-scales it. See the note on that describe
 *     block: an earlier `.max(100)` here rejected a valid 200 and blanked the
 *     whole /behaviour workspace.
 *
 * The fixtures below are trimmed copies of real responses captured from a
 * running backend, not invented shapes.
 */

import { describe, it, expect } from 'vitest';
import { OverviewSchema } from '@/lib/schemas/overview';
import { AnalyticsSchema } from '@/lib/schemas/analytics';
import { BehaviorScoreSchema, WELLNESS_SCORE_DOCUMENTED_MAX } from '@/lib/schemas/behavior-score';

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

describe('BehaviorScoreSchema — enforces the documented 0-100 contract', () => {
  const noDataPayload = {
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

  it('accepts the string-encoded Decimal the no-data fallback emits', () => {
    const result = BehaviorScoreSchema.safeParse(noDataPayload);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.score).toBe(100);
      expect(result.data.components.debt_health).toBe(1);
    }
  });

  /**
   * M10-A3 found this payload: with real transaction data the endpoint returned
   * `score: "7561.45"` instead of a 0-100 value, and M10 concluded the
   * validator must accept it because a `.max(100)` bound "rejects a valid HTTP
   * 200 and blanks the whole /behaviour workspace".
   *
   * That conclusion was correct about the RESPONSE being wrong and wrong about
   * the response being the contract. M11 fixed the authority instead:
   * `compute_financial_profile` was storing
   * `wellness_score_bps = int(wellness_score * 10000)` on a value that is
   * ALREADY 0-100 (`wellness.py:88-89`), so the basis-point column held
   * 0-1,000,000 instead of 0-10,000, and `BehaviourRepository._map_snapshot_row`
   * multiplied by 100 again on read. `behaviour_service.py` now stores
   * `int(wellness_score * 100)` and `run_migrations` rescales persisted rows
   * above 10000.
   *
   * The live response for the same seed data is now `score: "87.5400"` with
   * band `"Healthy"` (87.54 is in the 75-89 band), and every sibling column in
   * the same snapshot row was already a true basis-point value
   * (`cashflow_stability_score_bps` = 8230, `resilience_index_bps` = 9860).
   *
   * The bound is therefore restored. The payload below is what the authority
   * emitted BEFORE the backend fix; it is retained as a regression assertion
   * that a recurrence is now rejected rather than silently rendered.
   */
  const preFixPayload = {
    score: '7561.4500',
    band: 'Excellent',
    components: {
      cashflow_health: '59.1100',
      debt_health: '0.5',
      savings_behaviour: '87.0800',
      resilience: '57.1400',
      lifestyle_control: '1',
      credit_behaviour: '0.60',
    },
    snapshot_date: '2026-10-02',
    version: 1,
  };

  it('accepts the post-fix score the backend now returns', () => {
    const result = BehaviorScoreSchema.safeParse({
      ...preFixPayload,
      score: '87.5400',
      band: 'Healthy',
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.score).toBe(87.54);
      expect(result.data.score).toBeLessThanOrEqual(WELLNESS_SCORE_DOCUMENTED_MAX);
      expect(result.data.band).toBe('Healthy');
    }
  });

  it('REJECTS the double-scaled score the backend used to return', () => {
    expect(BehaviorScoreSchema.safeParse(preFixPayload).success).toBe(false);
  });

  it('rejects a score above the documented maximum', () => {
    expect(
      BehaviorScoreSchema.safeParse({ ...preFixPayload, score: '100.01', band: 'Excellent' })
        .success,
    ).toBe(false);
  });

  it('accepts the exact documented boundaries', () => {
    expect(BehaviorScoreSchema.safeParse({ ...preFixPayload, score: '0', band: 'Critical' }).success).toBe(true);
    expect(
      BehaviorScoreSchema.safeParse({ ...preFixPayload, score: '100', band: 'Excellent' }).success,
    ).toBe(true);
  });

  it('still rejects a score that is not a number', () => {
    expect(BehaviorScoreSchema.safeParse({ ...preFixPayload, score: 'excellent' }).success).toBe(false);
  });

  it('still enforces the documented 0-100 range on components', () => {
    expect(
      BehaviorScoreSchema.safeParse({
        ...preFixPayload,
        score: '87.54',
        components: { ...preFixPayload.components, cashflow_health: '5955' },
      }).success,
    ).toBe(false);
  });
});
