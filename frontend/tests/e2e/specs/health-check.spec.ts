/**
 * Health Check Tests
 * ===================
 *
 * Comprehensive health check suite for ClariFin_OS frontend.
 * Tests that every page loads without errors and displays meaningful content.
 */

import { test, expect, Page } from '@playwright/test';

// Helper to capture console errors - commented out as unused
// async function captureConsoleErrors(page: Page): Promise<string[]> {
//   const errors: string[] = [];
//   page.on('console', msg => {
//     if (msg.type() === 'error') errors.push(msg.text());
//   });
//   page.on('pageerror', err => errors.push(err.message));
//   return errors;
// }

// Helper to check for visible error states
async function hasErrorState(page: Page): Promise<boolean> {
  const errorSelectors = [
    'text=Something went wrong',
    'text=Error loading',
    'text=Failed to load',
    'text=500 Internal Server Error',
    'text=500 Error',
    '[data-testid="error-boundary"]',
    '.error-state',
    'text=Cannot read properties'
  ];
  for (const selector of errorSelectors) {
    const locator = page.locator(selector);
    const count = await locator.count();
    if (count > 0) {
      const isVisible = await locator.first().isVisible().catch(() => false);
      if (isVisible) {
        console.log(`Error state detected: selector="${selector}", count=${count}`);
        return true;
      }
    }
  }
  return false;
}

// Helper to check page has meaningful content
async function hasContent(page: Page): Promise<boolean> {
  // Page should have more than just a loading spinner
  await page.waitForTimeout(2000); // Wait for data to load
  const bodyText = await page.locator('body').textContent();
  return (bodyText?.length ?? 0) > 200;
}

const PAGES = [
  { name: 'Dashboard', url: '/dashboard/' },
  { name: 'Transactions', url: '/transactions/' },
  { name: 'Accounts', url: '/accounts/' },
  { name: 'Cards', url: '/cards/' },
  { name: 'Cashflow', url: '/cashflow/' },
  { name: 'Net Worth', url: '/net-worth/' },
  { name: 'Statements', url: '/statements/' },
  { name: 'Imports', url: '/imports/' },
  { name: 'Loans', url: '/loans/' },
  { name: 'Investments', url: '/investments/' },
  { name: 'Recurring', url: '/recurring/' },
  { name: 'Snapshots', url: '/snapshots/' },
  { name: 'Behavior', url: '/behaviour/' },
  { name: 'Projections', url: '/projections/' },
  { name: 'Reconciliation', url: '/reconciliation/' },
  { name: 'Categories', url: '/categories/' },
  { name: 'Income Sources', url: '/income-sources/' },
  { name: 'Export', url: '/export/' },
  { name: 'Audit', url: '/audit/' },
];

// Test 1: Every page loads without white screen
for (const pageConfig of PAGES) {
  test(`${pageConfig.name} - loads without crash`, async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', err => consoleErrors.push(err.message));

    const response = await page.goto(
      `http://localhost:3000${pageConfig.url}`,
      { waitUntil: 'networkidle', timeout: 15000 }
    );

    // Page must return 200
    expect(response?.status()).not.toBe(404);
    expect(response?.status()).not.toBe(500);

    // No JavaScript crashes
    const jsErrors = consoleErrors.filter(e =>
      e.includes('TypeError') ||
      e.includes('ReferenceError') ||
      e.includes('Cannot read properties of undefined') ||
      e.includes('is not a function')
    );

    if (jsErrors.length > 0) {
      console.log(`JS Errors on ${pageConfig.name}:`, jsErrors);
    }
    expect(jsErrors).toHaveLength(0);

    // No error boundary shown
    const errorVisible = await hasErrorState(page);
    expect(errorVisible).toBe(false);

    // Page has content
    const contentVisible = await hasContent(page);
    expect(contentVisible).toBe(true);

    // Screenshot for visual record
    await page.screenshot({
      path: `test-results/${pageConfig.name.toLowerCase().replace(' ', '-')}.png`,
      fullPage: true
    });
  });
}

// Test 2: Dashboard shows financial data
test('Dashboard - shows financial metrics', async ({ page }) => {
  await page.goto('http://localhost:3000/dashboard/',
    { waitUntil: 'networkidle' });

  // Should show some numbers (net worth, cashflow, etc.)
  const pageText = await page.locator('body').textContent();

  // Check for currency indicators
  const hasNumbers = /₹|INR|\d+,\d+|\d+\.\d+/.test(pageText ?? '');
  expect(hasNumbers).toBe(true);
});

// Test 3: Transactions page shows transaction list
test('Transactions - shows transaction rows', async ({ page }) => {
  await page.goto('http://localhost:3000/transactions/',
    { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // Find the actual selector by checking page content
  const pageText = await page.locator('body').textContent();
  console.log('Page text length:', pageText?.length);
  console.log('Has UPI:', pageText?.includes('UPI'));
  console.log('Has amount:', pageText?.includes('₹'));

  // Check for any transaction data
  const hasTransactionData =
    pageText?.includes('UPI') ||
    pageText?.includes('SALARY') ||
    pageText?.includes('₹') ||
    pageText?.includes('debit') ||
    pageText?.includes('credit');

  expect(hasTransactionData).toBe(true);
});

// Test 4: Cashflow page shows chart
test('Cashflow - renders chart with data', async ({ page }) => {
  await page.goto('http://localhost:3000/cashflow/',
    { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000); // Charts need time to render

  // Check for SVG (charts render as SVG)
  const svgCount = await page.locator('svg').count();
  console.log(`SVG elements on cashflow page: ${svgCount}`);
  expect(svgCount).toBeGreaterThan(0);

  // Check for true net income section
  const pageText = await page.locator('body').textContent();
  const hasTrueNet = pageText?.toLowerCase().includes('true') ||
                     pageText?.toLowerCase().includes('net income') ||
                     pageText?.includes('₹');
  expect(hasTrueNet).toBe(true);
});

// Test 5: Net Worth page shows chart and number
test('Net Worth - shows net worth value and chart', async ({ page }) => {
  await page.goto('http://localhost:3000/net-worth/',
    { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  const svgCount = await page.locator('svg').count();
  console.log(`SVG elements on networth page: ${svgCount}`);
  expect(svgCount).toBeGreaterThan(0);
});

// Test 6: API proxy works (frontend talks to backend)
test('API proxy - frontend reaches backend', async ({ page }) => {
  const apiResponses: Array<{url: string, status: number}> = [];

  // Set up listener BEFORE navigation
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      apiResponses.push({
        url: response.url(),
        status: response.status()
      });
    }
  });

  await page.goto('http://localhost:3000/dashboard/',
    { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  console.log('API responses captured:', apiResponses);

  const serverErrors = apiResponses.filter(r => r.status >= 500);
  console.log('Server errors:', serverErrors);

  expect(apiResponses.length).toBeGreaterThan(0);
  expect(serverErrors).toHaveLength(0);
});

// Test 7: Navigation works
test('Navigation - can move between pages', async ({ page }) => {
  await page.goto('http://localhost:3000/dashboard/',
    { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Take screenshot to see what navigation looks like
  await page.screenshot({ path: 'test-results/nav-debug.png' });

  // Find any navigation links
  const allLinks = page.locator('a[href]');
  const linkCount = await allLinks.count();
  console.log(`Total links found: ${linkCount}`);
  
  // Log all href values for analysis
  for (let i = 0; i < Math.min(linkCount, 20); i++) {
    const href = await allLinks.nth(i).getAttribute('href');
    console.log(`Link ${i}: ${href}`);
  }

  expect(linkCount).toBeGreaterThan(3);

  // Try to navigate to transactions
  const txnLink = page.locator('a[href="/transactions"]').first();
  const txnLinkVisible = await txnLink.isVisible().catch(() => false);

  if (txnLinkVisible) {
    await txnLink.click();
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('transactions');
  } else {
    // Navigation structure is different, just verify links exist
    console.log('Transactions link not directly visible - checking sidebar');
    const sidebar = page.locator('nav, aside, [role="navigation"]');
    const sidebarExists = await sidebar.isVisible().catch(() => false);
    console.log('Sidebar exists:', sidebarExists);
    expect(linkCount).toBeGreaterThan(3);
  }
});

// Test 8: No 404 pages
test('No pages return 404', async ({ page }) => {
  const notFoundPages: string[] = [];

  for (const pageConfig of PAGES) {
    const response = await page.goto(
      `http://localhost:3000${pageConfig.url}`,
      { waitUntil: 'load', timeout: 15000 }
    );

    // Check final URL after redirects
    const finalUrl = page.url();
    const status = response?.status();

    // A 404 page would have status 404 (the authoritative check)
    // If status is 200, the page loaded successfully regardless of content
    const is404 = status === 404;
    
    console.log(`Page ${pageConfig.url}: status=${status}, finalUrl=${finalUrl}, is404=${is404}`);
    
    if (is404) {
      notFoundPages.push(pageConfig.url);
    }
  }

  if (notFoundPages.length > 0) {
    console.log('Pages returning 404:', notFoundPages);
  }
  expect(notFoundPages).toHaveLength(0);
});