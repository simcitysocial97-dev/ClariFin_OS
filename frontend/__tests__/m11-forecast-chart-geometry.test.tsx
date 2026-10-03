/**
 * M11 — Forecast chart geometry must never emit NaN.
 *
 * Defect under regression
 * -----------------------
 * `/forecast` emitted SVG geometry the browser rejected:
 *
 *   Error: <path> attribute d: Expected number, "M 10,NaN 44.545454545…"
 *   Error: <polyline> attribute points: Expected number, "10,NaN 44.54545…"
 *
 * Three causes: `i / (length - 1)` with a single point, `(v - min) / range`
 * with a zero range, and non-finite values propagating from the backend.
 *
 * This test asserts on the RENDERED SVG, not on the arithmetic that feeds it:
 * it scans every geometry-bearing attribute for a value an SVG parser would
 * reject, which is what the browser reported.
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  classifySample,
  DEFAULT_VIEWPORT,
  describeRejections,
  isParseableGeometry,
  projectSeries,
  toPathData,
  toPolylinePoints,
} from '@/lib/visualization/chart-geometry';
import { CashflowProjection } from '@/components/forecast/cashflow-projection';
import { NetWorthProjection } from '@/components/forecast/net-worth-projection';
import type {
  CashflowProjectionViewModel,
  NetWorthProjectionViewModel,
} from '@/types/forecast-view-model';

/** Attribute names that carry SVG geometry. */
const GEOMETRY_ATTRIBUTES = ['d', 'points', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'width', 'height'];

/**
 * Every geometry attribute in the rendered tree, as `[element, attribute, value]`.
 *
 * The invalid-value tokens the browser rejects are checked literally, so this
 * scans the whole subtree rather than only the elements a selector names.
 */
function geometryAttributes(container: HTMLElement): { name: string; value: string }[] {
  const found: { name: string; value: string }[] = [];
  const all = container.querySelectorAll('*');
  all.forEach((element) => {
    GEOMETRY_ATTRIBUTES.forEach((attr) => {
      const value = element.getAttribute(attr);
      if (value !== null) {
        found.push({ name: `${element.tagName.toLowerCase()}@${attr}`, value });
      }
    });
  });
  return found;
}

/** Fail if any geometry attribute carries a token an SVG parser rejects. */
function expectNoInvalidGeometry(container: HTMLElement) {
  const offenders = geometryAttributes(container).filter(({ value }) =>
    /NaN|Infinity|undefined|null/i.test(value)
  );
  expect(offenders).toEqual([]);
}

// ==================================================================
// Series that reproduce each NaN cause
// ==================================================================

const VALID_SERIES = [100, 220, 180, 300, 260];
const FLAT_SERIES = [0, 0, 0, 0, 0];
const SINGLE_POINT: number[] = [500];
const EMPTY: number[] = [];
const INVALID_VALUES: unknown[] = [
  100,
  null,
  220,
  'not-a-number',
  Number.NaN,
  300,
  Number.POSITIVE_INFINITY,
  180,
];

// ==================================================================
// Unit level: the geometry primitive is total
// ==================================================================

describe('chart-geometry: finite output for every input', () => {
  it('single point does not divide by zero', () => {
    const result = projectSeries(SINGLE_POINT);
    expect(result.isSinglePoint).toBe(true);
    expect(Number.isFinite(result.samples[0].x)).toBe(true);
    expect(Number.isFinite(result.samples[0].y)).toBe(true);
  });

  it('a zero range does not divide by zero', () => {
    const result = projectSeries(FLAT_SERIES);
    expect(result.isDegenerateRange).toBe(true);
    result.samples.forEach((sample) => {
      expect(Number.isFinite(sample.x)).toBe(true);
      expect(Number.isFinite(sample.y)).toBe(true);
    });
  });

  it('an empty series yields nothing and reports it', () => {
    const result = projectSeries(EMPTY);
    expect(result.isEmpty).toBe(true);
    expect(result.samples).toEqual([]);
    expect(result.valueRange).toBeNull();
  });

  it('invalid backend values are rejected, not coerced', () => {
    const result = projectSeries(INVALID_VALUES);
    expect(result.samples.every((s) => Number.isFinite(s.x) && Number.isFinite(s.y))).toBe(true);
    expect(result.rejected).toHaveLength(4);
    expect(result.rejected.map((r) => r.reason).sort()).toEqual([
      'not-a-number',
      'not-a-number',
      'not-finite',
      'not-finite',
    ]);
    // The rejected values must not have been replaced with a plausible number.
    expect(result.samples.map((s) => s.value).sort((a, b) => a - b)).toEqual([100, 180, 220, 300]);
  });

  it('a fully invalid series is empty, not a chart of substituted values', () => {
    const result = projectSeries([Number.NaN, 'x', null, Number.POSITIVE_INFINITY]);
    expect(result.isEmpty).toBe(true);
    expect(result.rejected).toHaveLength(4);
  });

  it('polyline and path are empty below two points', () => {
    expect(toPolylinePoints([])).toBe('');
    expect(toPolylinePoints(projectSeries(SINGLE_POINT).samples)).toBe('');
    expect(toPathData([])).toBe('');
    expect(toPathData(projectSeries(SINGLE_POINT).samples)).toBe('');
  });

  it('every emitted geometry string is parseable', () => {
    [VALID_SERIES, FLAT_SERIES, SINGLE_POINT, EMPTY, INVALID_VALUES].forEach((series) => {
      const { samples } = projectSeries(series as unknown[]);
      expect(isParseableGeometry(toPolylinePoints(samples))).toBe(true);
      expect(isParseableGeometry(toPathData(samples))).toBe(true);
    });
  });

  it('classifySample separates the two rejection reasons', () => {
    expect(classifySample(1)).toBeNull();
    expect(classifySample(0)).toBeNull();
    expect(classifySample(Number.NaN)).toBe('not-finite');
    expect(classifySample(Number.POSITIVE_INFINITY)).toBe('not-finite');
    expect(classifySample('1')).toBe('not-a-number');
    expect(classifySample(null)).toBe('not-a-number');
    expect(classifySample(undefined)).toBe('not-a-number');
    expect(classifySample({})).toBe('not-a-number');
  });

  it('describeRejections summarises what was dropped', () => {
    expect(describeRejections([])).toBe('');
    expect(describeRejections(projectSeries(INVALID_VALUES).rejected)).toBe(
      '2 non-numeric and 2 non-finite'
    );
  });

  it('a custom viewport is respected and still finite', () => {
    const result = projectSeries(VALID_SERIES, { ...DEFAULT_VIEWPORT, width: 0, height: 0 });
    result.samples.forEach((s) => {
      expect(Number.isFinite(s.x)).toBe(true);
      expect(Number.isFinite(s.y)).toBe(true);
    });
  });
});

// ==================================================================
// Component level: the rendered SVG
// ==================================================================

const netWorthRows: NetWorthProjectionViewModel[] = VALID_SERIES.map((value, i) => ({
  date: `2026-${String(i + 1).padStart(2, '0')}-01`,
  projected_paise: value,
  lower_bound_paise: value - 10,
  upper_bound_paise: value + 10,
}));

const cashflowRows: CashflowProjectionViewModel[] = [
  { month: '2026-04', income_paise: 800000, expenses_paise: 300000, net_paise: 500000 },
  { month: '2026-05', income_paise: 820000, expenses_paise: 310000, net_paise: 510000 },
  { month: '2026-06', income_paise: 790000, expenses_paise: 295000, net_paise: 495000 },
];

describe('NetWorthProjection: no NaN geometry is emitted', () => {
  it('valid populated data', () => {
    const { container } = render(
      <NetWorthProjection projections={netWorthRows} loading={false} error={null} />
    );
    expectNoInvalidGeometry(container);
    expect(screen.getByTestId('net-worth-projection-chart')).toBeInTheDocument();
  });

  it('a flat series (zero range)', () => {
    const flat = netWorthRows.map((row) => ({ ...row, projected_paise: 0 }));
    const { container } = render(
      <NetWorthProjection projections={flat} loading={false} error={null} />
    );
    expectNoInvalidGeometry(container);
    expect(screen.getByTestId('net-worth-projection-flat')).toBeInTheDocument();
  });

  it('a single point', () => {
    const { container } = render(
      <NetWorthProjection projections={[netWorthRows[0]]} loading={false} error={null} />
    );
    expectNoInvalidGeometry(container);
    expect(screen.getByTestId('net-worth-projection-single-point')).toBeInTheDocument();
    expect(container.querySelector('polyline')).toBeNull();
  });

  it('invalid backend data is disclosed and not drawn', () => {
    const corrupt = [
      { ...netWorthRows[0], projected_paise: Number.NaN as unknown as number },
      netWorthRows[1],
      { ...netWorthRows[2], projected_paise: 'x' as unknown as number },
      netWorthRows[3],
      { ...netWorthRows[4], projected_paise: null as unknown as number },
    ];
    const { container } = render(
      <NetWorthProjection projections={corrupt} loading={false} error={null} />
    );
    expectNoInvalidGeometry(container);
    expect(screen.getByTestId('net-worth-projection-rejected')).toBeInTheDocument();
  });

  it('loading state emits no geometry at all', () => {
    render(<NetWorthProjection projections={netWorthRows} loading error={null} />);
    expect(screen.queryByTestId('net-worth-projection-chart')).toBeNull();
  });

  it('error state emits no geometry', () => {
    render(
      <NetWorthProjection projections={netWorthRows} loading={false} error={new Error('boom')} />
    );
    expect(screen.queryByTestId('net-worth-projection-chart')).toBeNull();
    expect(screen.getByText('Failed to load net worth projection')).toBeInTheDocument();
  });

  it('empty state emits no geometry', () => {
    render(<NetWorthProjection projections={[]} loading={false} error={null} />);
    expect(screen.queryByTestId('net-worth-projection-chart')).toBeNull();
    expect(screen.getByText('No projection data available')).toBeInTheDocument();
  });
});

describe('CashflowProjection: no NaN geometry is emitted', () => {
  it('valid populated data', () => {
    const { container } = render(
      <CashflowProjection
        projections={cashflowRows}
        basis={{
          status: 'available',
          model: 'v1.0-weightedaverage',
          historyMonths: 3,
          projectedMonths: 3,
          confidenceBps: 9700,
        }}
        loading={false}
        error={null}
      />
    );
    expectNoInvalidGeometry(container);
    expect(screen.getByTestId('cashflow-projection-chart')).toBeInTheDocument();
    expect(screen.getByTestId('cashflow-projection-provenance')).toHaveTextContent(
      'v1.0-weightedaverage'
    );
  });

  it('an all-zero series does not divide by zero', () => {
    const zeroed = cashflowRows.map((row) => ({
      ...row,
      income_paise: 0,
      expenses_paise: 0,
      net_paise: 0,
    }));
    const { container } = render(
      <CashflowProjection projections={zeroed} loading={false} error={null} />
    );
    expectNoInvalidGeometry(container);
  });

  it('a single month does not divide by zero', () => {
    const { container } = render(
      <CashflowProjection projections={[cashflowRows[0]]} loading={false} error={null} />
    );
    expectNoInvalidGeometry(container);
  });

  it('invalid backend data is disclosed and not drawn', () => {
    const corrupt = [
      { ...cashflowRows[0], income_paise: Number.NaN as unknown as number },
      { ...cashflowRows[1], expenses_paise: 'x' as unknown as number },
      cashflowRows[2],
    ];
    const { container } = render(
      <CashflowProjection projections={corrupt} loading={false} error={null} />
    );
    expectNoInvalidGeometry(container);
    expect(screen.getByTestId('cashflow-projection-rejected')).toBeInTheDocument();
  });

  it('a disclosed truncation caveat is rendered', () => {
    const { container } = render(
      <CashflowProjection
        projections={cashflowRows}
        basis={{
          status: 'available',
          reason: 'Requested 24 months; the model projects at most 12.',
          historyMonths: 3,
          projectedMonths: 3,
        }}
        loading={false}
        error={null}
      />
    );
    expectNoInvalidGeometry(container);
    expect(screen.getByTestId('cashflow-projection-note')).toHaveTextContent(
      'projects at most 12'
    );
  });

  it('an explicitly unavailable forecast renders a stated unavailable state', () => {
    render(
      <CashflowProjection
        projections={[]}
        basis={{
          status: 'unavailable',
          reason: 'Cashflow forecasting needs at least 2 measured months; 0 recorded.',
          historyMonths: 0,
        }}
        loading={false}
        error={null}
      />
    );
    expect(screen.queryByTestId('cashflow-projection-chart')).toBeNull();
    const state = screen.getByTestId('cashflow-projection-unavailable');
    expect(state).toHaveTextContent('Cashflow forecasting unavailable');
    expect(state).toHaveTextContent('needs at least 2 measured months');
  });

  it('an unavailable forecast with no series still states unavailability', () => {
    render(
      <CashflowProjection
        projections={[]}
        basis={{ status: 'unavailable', historyMonths: 1 }}
        loading={false}
        error={null}
      />
    );
    expect(screen.getByTestId('cashflow-projection-unavailable')).toBeInTheDocument();
  });

  it('an empty series with no basis at all does not claim a zero projection', () => {
    render(<CashflowProjection projections={[]} loading={false} error={null} />);
    expect(screen.queryByTestId('cashflow-projection-chart')).toBeNull();
    expect(screen.getByTestId('cashflow-projection-unavailable')).toBeInTheDocument();
  });

  it('loading and error states emit no geometry', () => {
    const loading = render(
      <CashflowProjection projections={cashflowRows} loading error={null} />
    );
    expect(loading.container.querySelector('[data-testid="cashflow-projection-chart"]')).toBeNull();
    loading.unmount();

    const failed = render(
      <CashflowProjection projections={cashflowRows} loading={false} error={new Error('x')} />
    );
    expect(failed.container.querySelector('[data-testid="cashflow-projection-chart"]')).toBeNull();
    expect(screen.getByText('Failed to load cashflow projection')).toBeInTheDocument();
  });
});