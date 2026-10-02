/**
 * Platform Console independence and honesty — M10-A3
 *
 * These are the invariants behind the fixes made in this consolidation pass.
 * Each test names the defect it prevents from returning; none of them restate
 * a component's internals, they all assert observable behaviour.
 *
 * Background: `app/platform/layout.tsx` states the console must be usable
 * BEFORE the financial application is opened, and that it carries "no financial
 * data or controls". Before this pass, every `/platform/**` page issued
 * `GET /api/v1/members` through the root-layout `MemberProvider`, so the console
 * was in fact coupled to the financial API.
 */

import { test, expect } from '@playwright/test';

test.describe.configure({ timeout: 180_000 });

const BASE_URL = 'http://localhost:3000';
const PLATFORM_BASE = `${BASE_URL}/platform`;
const CONSOLE_TIMEOUT = 60_000;

/** A terminal console state: real data, explicit empty, or explicit unavailable. */
const CONSOLE_RESOLVED = [
  '[data-testid="platform-dashboard"]',
  '[data-testid="health-report"]',
  '[data-testid="workflow-inventory"]',
  '[data-testid="run-inventory"]',
  '[data-testid="capabilities-index"]',
  '[data-testid="diagnostics-report"]',
  '[data-testid="verification-state"]',
  '[data-testid="evidence-index"]',
  '[data-testid="compare-no-run-selected"]',
  '[data-testid="console-empty"]',
  '[data-testid="console-unavailable"]',
].join(', ');

async function gotoConsole(page: import('@playwright/test').Page, path: string) {
  await page.goto(`${PLATFORM_BASE}${path}`, { waitUntil: 'domcontentloaded', timeout: CONSOLE_TIMEOUT });
  await page.waitForSelector(CONSOLE_RESOLVED, { timeout: CONSOLE_TIMEOUT });
}

/**
 * CONSOLE INDEPENDENCE
 *
 * The console may call the platform verification API and nothing else. A request
 * to the financial application API (`/api/v1/...`, which is where every account,
 * transaction, loan, investment and member endpoint lives) means the console is
 * not standalone.
 */
const CONSOLE_ROUTES = [
  '',
  '/health',
  '/verification',
  '/diagnostics',
  '/diagnostics/change',
  '/workflows',
  '/capabilities',
  '/runs',
  '/runs/some-run-id',
  '/evidence',
  '/framework',
  '/architecture',
  '/errors',
  '/history',
  '/history/compare',
  '/capabilities/discover.blast-radius',
];

test.describe('Platform Console — independence from the financial application', () => {
  for (const route of CONSOLE_ROUTES) {
    test(`no financial-application request on ${route || '/platform'}`, async ({ page }) => {
      const financialRequests: string[] = [];
      const onRequest = (request: import('@playwright/test').Request) => {
        const url = request.url();
        if (url.includes('/api/v1/')) financialRequests.push(url);
      };
      page.on('request', onRequest);

      // Navigation is attempted even when the page stays in a loading or error
      // state: the invariant is about what the page asks for, not about whether
      // the backend happened to answer.
      await page.goto(`${PLATFORM_BASE}${route}`, { waitUntil: 'domcontentloaded', timeout: CONSOLE_TIMEOUT });
      await page.waitForTimeout(8000);
      page.off('request', onRequest);

      expect(financialRequests, `console must not call the financial API`).toEqual([]);
    });
  }
});

/**
 * NO CALLS TO ENDPOINTS THE BACKEND DOES NOT EXPOSE
 *
 * `/platform/v1/diagnostics/signatures` was requested by both the diagnostics
 * detail page and the `useDiagnosticSignatures` hook. The platform router has
 * `/diagnostics` (GET), `/diagnose` (POST) and `/diagnose/register` (POST) and no
 * signatures route, so every load 404'd and the "Failure Signature" section
 * could never render. The store is served by this app's own
 * `/api/diagnostic-signatures` route handler.
 */
test.describe('Platform Console — no calls to non-existent endpoints', () => {
  test('diagnostic detail reads the local signature store, not the backend', async ({ page }) => {
    const paths: string[] = [];
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/diagnostics/signatures') || url.includes('/api/diagnostic-signatures')) {
        paths.push(url.replace('http://localhost:8000', ''));
      }
    });

    await page.goto(`${PLATFORM_BASE}/diagnostics/detail/sig-70bebf3aa98d`, {
      waitUntil: 'domcontentloaded',
      timeout: CONSOLE_TIMEOUT,
    });
    await page.waitForTimeout(8000);

    expect(paths, 'must not request the non-existent backend signatures route').toEqual([]);
  });
});

/**
 * NO DEAD INTERNAL LINKS
 *
 * `QuickActions` linked to `/platform/settings`, a route that has never existed,
 * and a dead `<Link>` target is worse than a dead one because Next prefetches it
 * with an RSC request that never completes. Every console link must resolve.
 */
test.describe('Platform Console — internal links resolve', () => {
  test('every dashboard action link points at a real console page', async ({ page }) => {
    await gotoConsole(page, '');

    const hrefs = await page.evaluate(() =>
      Array.from(document.querySelectorAll('a[href^="/platform"]')).map((a) =>
        (a as HTMLAnchorElement).getAttribute('href')!,
      ),
    );
    expect(hrefs.length).toBeGreaterThan(0);

    for (const href of new Set(hrefs)) {
      const response = await page.request.get(`${BASE_URL}${href}`, {
        maxRedirects: 0,
        timeout: CONSOLE_TIMEOUT,
      });
      expect(response.status(), `${href} must not be a dead link`).not.toBe(404);
    }
  });
});

/**
 * HEALTH DIMENSIONS REPORT THE AUTHORITY'S OWN STATUS
 *
 * The dashboard resolved each dimension's badge by looking its label up in
 * `data.domains`, which only carries the sub-authority breakdown (Verification,
 * EventStore, Framework Integrity). Seven of eight badges therefore read UNKNOWN
 * while the API reported HEALTHY / SAFE / CURRENT / VALID / READY. The console
 * must not discard what the authority told it.
 */
test.describe('Platform Console — dashboard health dimensions', () => {
  test('every dimension renders a status, never UNKNOWN', async ({ page }) => {
    await gotoConsole(page, '');

    const labels = ['BACKEND', 'FRONTEND', 'DATABASE', 'ARCHITECTURE', 'VERIFICATION', 'EVIDENCE', 'AI RUNTIME', 'FRAMEWORK INTEGRITY'];
    for (const label of labels) {
      await expect(page.getByText(label, { exact: true })).toBeVisible();
    }

    const statuses = await page.evaluate(() =>
      Array.from(document.querySelectorAll('[data-testid="health-status-badge"]')).map((e) =>
        e.getAttribute('data-status'),
      ),
    );
    expect(statuses.length).toBeGreaterThanOrEqual(labels.length);
    expect(statuses, 'no dimension may be rendered UNKNOWN while the API has a status').not.toContain('UNKNOWN');
  });
});

/**
 * A DIRECT NAVIGATION TO THE COMPARE ROUTE MUST EXPLAIN ITSELF
 *
 * `/platform/history/compare` is only ever reached with `?current=<runId>`, so
 * reaching it directly rendered a bare "Run Comparison" heading: the query is
 * disabled without the parameter, so no loading, error or empty state could
 * appear and an operator could not distinguish a working page from a broken one.
 */
test.describe('Platform Console — compare route entry state', () => {
  test('direct navigation states that no run is selected', async ({ page }) => {
    await page.goto(`${PLATFORM_BASE}/history/compare`, {
      waitUntil: 'domcontentloaded',
      timeout: CONSOLE_TIMEOUT,
    });
    await expect(page.getByTestId('compare-no-run-selected')).toBeVisible();
  });
});

/**
 * A MISSING CAPABILITY MUST READ AS A FAILURE, NOT AS RAW JSON
 *
 * `/platform/verification/[capability]` rendered `String(detail.error)`, which
 * for the canonical `ApiError` is the stringified object — status, transient
 * flag and the fully escaped response envelope. The console now reports the
 * authority's own message through its standard terminal state.
 */
test.describe('Platform Console — error states are readable', () => {
  test('an unknown capability shows the unavailable state, not a serialised error', async ({ page }) => {
    await page.goto(`${PLATFORM_BASE}/verification/definitely-not-a-capability`, {
      waitUntil: 'domcontentloaded',
      timeout: CONSOLE_TIMEOUT,
    });
    await page.waitForSelector('[data-testid="console-unavailable"]', { timeout: CONSOLE_TIMEOUT });

    const text = await page.evaluate(() => document.body.innerText);
    expect(text).not.toContain('"transient"');
    expect(text).not.toContain('API 404 /platform');
    await expect(page.getByRole('button', { name: /retry/i })).toBeVisible();
  });
});
