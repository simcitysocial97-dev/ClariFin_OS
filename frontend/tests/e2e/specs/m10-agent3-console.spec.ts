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

/**
 * Budget for reaching a resolved console state.
 *
 * The platform snapshot build is expensive and serialises behind other
 * requests: measured on this host, the first `/platform/v1/health` after a cold
 * start took 39 s, and a batch of five console requests each logged
 * `duration_ms=117218` behind it. This is the same ground
 * `platform-c67.2.spec.ts` documents when it raises its own budget to 120 s and
 * its inner wait to 90 s — and that spec's 90 s wait was observed to expire on
 * this host under a 4-worker run. No assertion is relaxed: a console that never
 * reaches a terminal state still fails, just later.
 */
const CONSOLE_RESOLVED_TIMEOUT = 120_000;

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

async function gotoResolvedConsole(page: import('@playwright/test').Page, path: string) {
  await page.goto(`${PLATFORM_BASE}${path}`, { waitUntil: 'domcontentloaded', timeout: CONSOLE_TIMEOUT });
  await page.waitForSelector(CONSOLE_RESOLVED, { timeout: CONSOLE_RESOLVED_TIMEOUT });
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
    const backendRoute: string[] = [];
    const localRoute: string[] = [];
    page.on('request', (request) => {
      const path = new URL(request.url()).pathname;
      if (path === '/platform/v1/diagnostics/signatures') backendRoute.push(path);
      if (path === '/api/diagnostic-signatures') localRoute.push(path);
    });

    await page.goto(`${PLATFORM_BASE}/diagnostics/detail/sig-70bebf3aa98d`, {
      waitUntil: 'domcontentloaded',
      timeout: CONSOLE_TIMEOUT,
    });
    await page.waitForTimeout(8000);

    expect(backendRoute, 'must not request the non-existent backend signatures route').toEqual([]);
    expect(localRoute.length, 'must read this app\u2019s own signature store route').toBeGreaterThan(0);
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
    // The link inventory is read from the shell, which renders client-side from
    // the sidebar and the dashboard's QuickActions row. It deliberately does
    // NOT wait for the data-driven panel: this assertion is about which routes
    // the console advertises, and making it depend on a data round trip would
    // couple it to backend latency that has nothing to do with the invariant
    // under test. `QuickActions` renders an unlabelled row of buttons, so the
    // wait is on the links themselves rather than on a heading.
    await page.goto(`${PLATFORM_BASE}/`, { waitUntil: 'domcontentloaded', timeout: CONSOLE_TIMEOUT });
    await page.waitForSelector('[data-testid="platform-title-bar"]', { timeout: CONSOLE_TIMEOUT });
    await page.waitForSelector('a[href^="/platform"]', { timeout: CONSOLE_TIMEOUT });

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
    // The dimension row is derived from the health snapshot, so this does wait
    // for the resolved dashboard panel on the same budget every other
    // data-driven console spec in this repo already declares.
    await gotoResolvedConsole(page, '/');

    // The labels are uppercased with CSS (`uppercase` class), so the DOM text
    // is "Backend" while `innerText` is "BACKEND". Matching is therefore
    // case-insensitive; asserting the DOM's own casing would couple the test to
    // whether the uppercase is a CSS transform or baked into the string.
    //
    // The grid is read through its own testid rather than a page-wide search.
    // CI proved why: this page also renders framework-integrity and
    // domain-detail badges that legitimately report UNKNOWN when the authority
    // has no data for them, so asserting across every badge on the page failed
    // for reasons outside the eight dimensions this test exists to protect.
    // The CI evidence was:
    //   ["UNKNOWN","HEALTHY","HEALTHY","HEALTHY","HEALTHY","SAFE","CURRENT",
    //    "VALID","READY","HEALTHY","UNKNOWN","UNKNOWN","HEALTHY","CURRENT"]
    // — every dimension badge is correctly HEALTHY/SAFE/CURRENT/VALID/READY.
    const labels = ['Backend', 'Frontend', 'Database', 'Architecture', 'Verification', 'Evidence', 'AI Runtime', 'Framework Integrity'];
    const grid = page.getByTestId('health-dimensions-grid');
    await expect(grid).toBeVisible();
    // allInnerTexts() returns CSS-rendered text and these labels carry
    // `uppercase`; getByText() matches DOM text instead.
    const rendered = (await page.getByTestId('health-dimension-label').allInnerTexts()).map((t) => t.trim());
    expect(rendered, 'every health dimension must be labelled').toHaveLength(labels.length);

    const statuses = await page.evaluate(() =>
      Array.from(
        document.querySelectorAll(
          '[data-testid="health-dimensions-grid"] [data-testid="health-status-badge"]',
        ),
      ).map((e) => e.getAttribute('data-status')),
    );
    expect(statuses.length).toBe(labels.length);
    expect(statuses, 'no health dimension may be rendered UNKNOWN while the API has a status').not.toContain('UNKNOWN');
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
    await page.waitForSelector('[data-testid="console-unavailable"]', { timeout: CONSOLE_RESOLVED_TIMEOUT });

    const text = await page.evaluate(() => document.body.innerText);
    expect(text).not.toContain('"transient"');
    expect(text).not.toContain('API 404 /platform');
    await expect(page.getByRole('button', { name: /retry/i })).toBeVisible();
  });
});
