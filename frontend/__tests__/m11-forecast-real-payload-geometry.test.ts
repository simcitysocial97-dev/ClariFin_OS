import { describe, expect, it } from 'vitest';
import {
  classifySample,
  isParseableGeometry,
  projectSeries,
  toPathData,
  toPolylinePoints,
} from '@/lib/visualization/chart-geometry';
import { FORECAST_PAYLOADS } from './fixtures/forecast-api-payloads';

const payloads = FORECAST_PAYLOADS;

const NAMES = Object.keys(payloads);

describe('real API output produces no NaN geometry', () => {
  it('captured every scenario', () => {
    expect(NAMES.length).toBeGreaterThanOrEqual(5);
  });

  NAMES.forEach((name) => {
    it(`${name}: net worth series is finite and parseable`, () => {
      const body = payloads[name];
      const values = body.net_worth_projections.map((p) => p.projected_paise);
      const result = projectSeries(values);

      expect(result.rejected).toEqual([]);
      result.samples.forEach((s) => {
        expect(Number.isFinite(s.x)).toBe(true);
        expect(Number.isFinite(s.y)).toBe(true);
      });

      const points = toPolylinePoints(result.samples);
      const d = toPathData(result.samples);
      expect(isParseableGeometry(points)).toBe(true);
      expect(isParseableGeometry(d)).toBe(true);
      // A single-point series must emit no line at all, not a degenerate one.
      if (result.samples.length < 2) {
        expect(points).toBe('');
        expect(d).toBe('');
      }
    });

    it(`${name}: cashflow series is finite and parseable`, () => {
      const body = payloads[name];
      const income = body.cashflow_projections.map((p) => p.income_paise);
      const expenses = body.cashflow_projections.map((p) => p.expenses_paise);

      [income, expenses].forEach((series) => {
        const result = projectSeries(series);
        expect(result.rejected).toEqual([]);
        result.samples.forEach((s) => {
          expect(Number.isFinite(s.x)).toBe(true);
          expect(Number.isFinite(s.y)).toBe(true);
        });
        expect(isParseableGeometry(toPolylinePoints(result.samples))).toBe(true);
      });
    });

    it(`${name}: confidence intervals are finite`, () => {
      payloads[name].confidence_intervals.forEach((interval) => {
        expect(classifySample(interval.lower_paise)).toBeNull();
        expect(classifySample(interval.upper_paise)).toBeNull();
        expect(Number.isFinite(interval.level)).toBe(true);
      });
    });

    it(`${name}: month keys are unique and values are integer paise`, () => {
      const body = payloads[name];
      const cfMonths = body.cashflow_projections.map((p) => p.month);
      expect(new Set(cfMonths).size).toBe(cfMonths.length);

      const nwMonths = body.net_worth_projections.map((p) => p.date.slice(0, 7));
      expect(new Set(nwMonths).size).toBe(nwMonths.length);

      body.cashflow_projections.forEach((p) => {
        expect(Number.isInteger(p.income_paise)).toBe(true);
        expect(Number.isInteger(p.expenses_paise)).toBe(true);
        expect(Number.isInteger(p.net_paise)).toBe(true);
      });
    });
  });

  it('an unavailable forecast carries a reason and no projections', () => {
    const empty = payloads['empty_db'];
    expect(empty.cashflow_forecast_basis.status).toBe('unavailable');
    expect(empty.cashflow_forecast_basis.reason).toBeTruthy();
    expect(empty.cashflow_projections).toEqual([]);
    expect(empty.confidence_intervals).toEqual([]);
  });

  it('an available forecast names its model and history', () => {
    const populated = payloads['populated_3months_h6'];
    expect(populated.cashflow_forecast_basis.status).toBe('available');
    expect(populated.cashflow_forecast_basis.model).toBe('v1.0-weightedaverage');
    expect(populated.cashflow_forecast_basis.history_months).toBe(3);
    expect(populated.cashflow_forecast_basis.projected_months).toBe(6);
  });

  it('a horizon beyond the model limit is disclosed, not silently truncated', () => {
    const wide = payloads['populated_3months_h60'];
    expect(wide.cashflow_forecast_basis.requested_horizon_months).toBe(60);
    expect(wide.cashflow_forecast_basis.projected_months).toBe(12);
    expect(wide.cashflow_forecast_basis.reason).toContain('12');
  });
});