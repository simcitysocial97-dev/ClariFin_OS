/**
 * M9-C38 — API Gateway Invariance Test
 * ======================================
 * Architectural contract: the API gateway (lib/api/gateway.ts) is the ONLY
 * module permitted to issue a raw HTTP `fetch` to the backend, and it is the
 * ONLY place that hard-codes the backend URL / NEXT_PUBLIC_API_URL resolution.
 *
 * Every UI / hook / capability / client must route through `apiFetch` /
 * `apiFetchJson`. This makes URL resolution, error classification and retry
 * semantics live in exactly one place (ownership model from C38.2).
 *
 * If a future change adds a raw `fetch(.../api/...)` or re-introduces a
 * scattered `localhost:8000` / NEXT_PUBLIC_API_URL literal, this test fails —
 * preventing silent gateway bypass (C38.4).
 */

import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'fs';
import { join, dirname, relative } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const FRONTEND_ROOT = join(__dirname, '..', '..');

const SCAN_REL_DIRS = ['lib', 'hooks', 'components', 'app'];

// Files explicitly permitted to contain a raw backend fetch / URL literal.
const ALLOWED_RAW_FETCH = new Set(['lib/api/gateway.ts']);
const ALLOWED_URL_LITERAL = new Set([
  'lib/api/gateway.ts',
  'tests/global-setup.ts', // Playwright test infra, not a frontend API consumer
]);

// Directories / file patterns excluded from the scan.
const SKIP_DIRS = new Set([
  'node_modules',
  '__tests__',
  'mocks',
  'fixtures',
  'tests',
  'test-results',
  '.next',
  'dist',
  'generated',
]);

function walk(dir: string, out: string[]): void {
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return;
  }
  for (const name of entries) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) {
      if (SKIP_DIRS.has(name)) continue;
      walk(full, out);
    } else if (st.isFile()) {
      if (!/\.(ts|tsx)$/.test(name)) continue;
      if (/\.(test|spec)\.(ts|tsx)$/.test(name)) continue;
      out.push(relative(FRONTEND_ROOT, full).split('\\').join('/'));
    }
  }
}

function read(rel: string): string {
  return readFileSync(join(FRONTEND_ROOT, rel), 'utf8');
}

// Standalone `fetch(` NOT preceded by a letter (so apiFetch/refetch are excluded).
const RAW_FETCH_RE = /(?<![A-Za-z])fetch\(/g;
const URL_LITERAL_RE = /localhost:8000|NEXT_PUBLIC_API_URL/g;

describe('API gateway invariance (C38.4)', () => {
  const files: string[] = [];
  for (const d of SCAN_REL_DIRS) {
    walk(join(FRONTEND_ROOT, d), files);
  }

  it('scans a non-trivial set of source files', () => {
    expect(files.length).toBeGreaterThan(20);
  });

  it('forbids raw backend fetch outside the gateway', () => {
    const violations: string[] = [];
    for (const f of files) {
      if (ALLOWED_RAW_FETCH.has(f)) continue;
      const src = read(f);
      const matches = src.match(RAW_FETCH_RE);
      if (matches && matches.length > 0) {
        violations.push(`${f} (${matches.length} raw fetch)`);
      }
    }
    expect(violations, `Raw fetch bypassing gateway:\n${violations.join('\n')}`).toEqual([]);
  });

  it('forbids scattered backend URL literals outside the gateway / test infra', () => {
    const violations: string[] = [];
    for (const f of files) {
      if (ALLOWED_URL_LITERAL.has(f)) continue;
      const src = read(f);
      const matches = src.match(URL_LITERAL_RE);
      if (matches && matches.length > 0) {
        violations.push(`${f} (${[...new Set(matches)].join(', ')})`);
      }
    }
    expect(violations, `Scattered backend URL literal:\n${violations.join('\n')}`).toEqual([]);
  });

  it('keeps the gateway as the single raw-fetch owner', () => {
    const src = read('lib/api/gateway.ts');
    const matches = src.match(RAW_FETCH_RE);
    expect(matches, 'gateway.ts must own the raw fetch transport').not.toBeNull();
    expect(matches!.length).toBeGreaterThan(0);
  });
});
