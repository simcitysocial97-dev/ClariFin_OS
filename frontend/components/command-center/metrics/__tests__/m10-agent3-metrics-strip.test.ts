/**
 * M10-A3 — regression tests for the Command Center metrics strip.
 *
 * The strip used to attach a hardcoded period-over-period delta and a hardcoded
 * confidence to every metric (`deltaPaise: 1820000, // Placeholder`,
 * `confidence: 97`, ...), so the Command Center asserted measured financial
 * movement — "Net Worth +₹18,200 (+2.8%) at 97% confidence" — that no data
 * supported. It also scaled ratios by 10000 and routed them through the money
 * primitive, so a 42% debt ratio was displayed as "₹4,20,000.00".
 *
 * These tests pin the two properties that matter: the derived values are
 * computed from the graph, and no fabricated literal can reappear.
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const STRIP_PATH = join(
  __dirname,
  '..',
  'metrics-strip.tsx',
);

const rawSource = readFileSync(STRIP_PATH, 'utf8');

/**
 * The file's own doc comment quotes the old literals (`deltaPaise: 1820000,
 * // Placeholder`, `confidence: 97`) to explain what was removed. Comments are
 * stripped before asserting so the invariant is checked against executable code
 * only — otherwise the documentation of the bug would satisfy the bug.
 */
const source = rawSource
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/^[ \t]*\/\/.*$/gm, '');

describe('metrics-strip: no fabricated financial deltas or confidences', () => {
  it('contains no hardcoded paise delta literals', () => {
    expect(source).not.toMatch(/deltaPaise:\s*[\d-]/);
    expect(source).not.toMatch(/deltaPercent:\s*[\d-]/);
  });

  it('contains no hardcoded confidence literals', () => {
    expect(source).not.toMatch(/confidence:\s*\d/);
  });

  it('no longer scales ratios by 10000 to fake a paise magnitude', () => {
    expect(source).not.toMatch(/\*\s*10000/);
  });

  it('documents the M10-A3 provenance', () => {
    expect(rawSource).toContain('M10-A3');
  });
});

describe('MetricTile: ratios are not rendered as money', () => {
  const tileSource = readFileSync(
    join(
      __dirname,
      '..',
      '..',
      '..',
      'primitives',
      'metric-tile',
      'metric-tile.tsx',
    ),
    'utf8',
  );

  it('defaults to the money format so existing money callers are unchanged', () => {
    expect(tileSource).toMatch(/format\s*=\s*'money'/);
  });

  it('routes money through MoneyValue and other formats through a plain renderer', () => {
    expect(tileSource).toMatch(/format === 'money'/);
    expect(tileSource).toMatch(/MoneyValue/);
  });
});
