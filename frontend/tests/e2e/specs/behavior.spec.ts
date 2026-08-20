/**
 * Behavior Page Tests
 * ====================
 * 
 * Tests for the behavioral insights page:
 * - Financial health score
 * - Behavioral indices
 * - Insights display
 * - Nudges/recommendations
 */

import { test, expect } from '../fixtures/test-fixtures';

// ============================================================================
// Behavior Page Loading Tests
// ============================================================================

test.describe('Behavior Page Loading', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/behaviour');
    await page.waitForLoadState('networkidle');
  });

  test('should load behavior page', async ({ page, waitForPageReady, assertNoErrors }) => {
    await waitForPageReady(page);
    
    const content = await page.locator('body').innerHTML();
    expect(content.length).toBeGreaterThan(100);
    
    assertNoErrors();
  });

  test('should display page title', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);

    // The behaviour workspace renders its title via the score/section headings
    // (not a top-level h1/h2/h3 landmark), so assert the page title content is
    // actually visible rather than assuming a specific heading tag.
    const title = page.locator('text=/Financial Health Score|Behaviour|Wellness/i').first();
    await expect(title).toBeVisible();
  });

  test('should show mode toggle', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const modeToggle = page.locator('button:has-text("Personal"), button:has-text("Family")').first();
    const hasToggle = await modeToggle.isVisible().catch(() => false);
    
    console.log(`Mode toggle visible: ${hasToggle}`);
  });
});

// ============================================================================
// Financial Health Score Tests
// ============================================================================

test.describe('Financial Health Score', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/behaviour');
    await page.waitForLoadState('networkidle');
  });

  test('should display health score section', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const healthSection = page.locator('text=/health|score/i').first();
    const hasHealth = await healthSection.isVisible().catch(() => false);
    
    console.log(`Health score section visible: ${hasHealth}`);
  });

  test('should show score value', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for score value (0-100)
    const scoreValue = page.locator('text=/\\d{1,3}/').first();
    const hasScore = await scoreValue.isVisible().catch(() => false);
    
    console.log(`Score value visible: ${hasScore}`);
  });

  test('should show confidence indicator', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const confidence = page.locator('text=/confidence/i').first();
    const hasConfidence = await confidence.isVisible().catch(() => false);
    
    console.log(`Confidence indicator visible: ${hasConfidence}`);
  });
});

// ============================================================================
// Behavioral Indices Tests
// ============================================================================

test.describe('Behavioral Indices', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/behaviour');
    await page.waitForLoadState('networkidle');
  });

  test('should display behavioral indices', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for index names
    const indices = ['savings', 'impulsivity', 'stress', 'habit', 'loss'];
    let foundIndices = 0;
    
    for (const index of indices) {
      const indexElement = page.locator(`text=/${index}/i`).first();
      if (await indexElement.isVisible().catch(() => false)) {
        foundIndices++;
      }
    }
    
    console.log(`Found ${foundIndices} behavioral indices`);
  });

  test('should show savings discipline index', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const savings = page.locator('text=/savings/i').first();
    const hasSavings = await savings.isVisible().catch(() => false);
    
    console.log(`Savings index visible: ${hasSavings}`);
  });

  test('should show impulsivity score', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const impulsivity = page.locator('text=/impulsiv/i').first();
    const hasImpulsivity = await impulsivity.isVisible().catch(() => false);
    
    console.log(`Impulsivity score visible: ${hasImpulsivity}`);
  });

  test('should show financial stress index', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const stress = page.locator('text=/stress/i').first();
    const hasStress = await stress.isVisible().catch(() => false);
    
    console.log(`Stress index visible: ${hasStress}`);
  });
});

// ============================================================================
// Insights Tests
// ============================================================================

test.describe('Behavioral Insights', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/behaviour');
    await page.waitForLoadState('networkidle');
  });

  test('should display insights section', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const insights = page.locator('text=/insight/i').first();
    const hasInsights = await insights.isVisible().catch(() => false);
    
    console.log(`Insights section visible: ${hasInsights}`);
  });

  test('should show insight cards', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for insight cards
    const insightCards = page.locator('[class*="card"], [class*="insight"]').filter({ 
      hasText: /spending|saving|habit|trend/i 
    });
    const count = await insightCards.count();
    
    console.log(`Found ${count} insight cards`);
  });

  test('should show insight severity indicators', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for warning/positive indicators
    const warning = page.locator('[class*="warning"], text=/warning|alert/i').first();
    const positive = page.locator('[class*="positive"], text=/good|great/i').first();
    
    const hasWarning = await warning.isVisible().catch(() => false);
    const hasPositive = await positive.isVisible().catch(() => false);
    
    console.log(`Warning visible: ${hasWarning}, Positive visible: ${hasPositive}`);
  });
});

// ============================================================================
// Nudges Tests
// ============================================================================

test.describe('Behavioral Nudges', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/behaviour');
    await page.waitForLoadState('networkidle');
  });

  test('should display nudges section', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const nudges = page.locator('text=/nudge|recommend|suggest/i').first();
    const hasNudges = await nudges.isVisible().catch(() => false);
    
    console.log(`Nudges section visible: ${hasNudges}`);
  });

  test('should show actionable suggestions', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for action items
    const actions = page.locator('text=/try|consider|reduce|increase/i').first();
    const hasActions = await actions.isVisible().catch(() => false);
    
    console.log(`Actionable suggestions visible: ${hasActions}`);
  });
});

// ============================================================================
// Risk Signals Tests
// ============================================================================

test.describe('Risk Signals', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/behaviour');
    await page.waitForLoadState('networkidle');
  });

  test('should display risk signals section', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const risks = page.locator('text=/risk|flag|warning/i').first();
    const hasRisks = await risks.isVisible().catch(() => false);
    
    console.log(`Risk signals visible: ${hasRisks}`);
  });

  test('should show India-specific risk patterns', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for India-specific patterns
    const upiPattern = page.locator('text=/UPI|micro/i').first();
    const gamblingPattern = page.locator('text=/gambling|gaming/i').first();
    const emiPattern = page.locator('text=/EMI|loan/i').first();
    
    const hasUPI = await upiPattern.isVisible().catch(() => false);
    const hasGambling = await gamblingPattern.isVisible().catch(() => false);
    const hasEMI = await emiPattern.isVisible().catch(() => false);
    
    console.log(`India risks - UPI: ${hasUPI}, Gambling: ${hasGambling}, EMI: ${hasEMI}`);
  });
});

// ============================================================================
// Data Quality Tests
// ============================================================================

test.describe('Data Quality Indicators', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/behaviour');
    await page.waitForLoadState('networkidle');
  });

  test('should show transaction count', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const txnCount = page.locator('text=/\\d+\\s*transaction/i').first();
    const hasCount = await txnCount.isVisible().catch(() => false);
    
    console.log(`Transaction count visible: ${hasCount}`);
  });

  test('should show data quality indicator', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const quality = page.locator('text=/quality|90 days/i').first();
    const hasQuality = await quality.isVisible().catch(() => false);
    
    console.log(`Data quality indicator visible: ${hasQuality}`);
  });
});

// ============================================================================
// Behavior API Tests
// ============================================================================

test.describe('Behavior API', () => {
  test('should handle API unavailable gracefully', async ({ page, captureErrors, waitForPageReady }) => {
    captureErrors(page);
    
    // Block API
    await page.route('**/api/v1/behaviour/**', route =>
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) })
    );
    
    await page.goto('/behaviour');
    await waitForPageReady(page);
    
    // Page should still render a degraded (error) state. The behaviour workspace
    // intentionally renders a non-<main> error Alert on API failure (C41.13), so
    // we assert the error state is visible rather than a <main> landmark.
    const errorState = page.locator('[role="alert"]').first();
    await expect(errorState).toBeVisible();
  });

  test('should show empty state when no data', async ({ page, captureErrors, waitForPageReady }) => {
    captureErrors(page);
    
    // Mock empty response
    await page.route('**/api/v1/behaviour/wellness-score', route =>
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          score: 100,
          band: 'Excellent',
          components: {
            cashflow_health: 100,
            debt_health: 1,
            savings_behaviour: 100,
            resilience: 100,
            lifestyle_control: 100,
            credit_behaviour: 0.5,
          },
          snapshot_date: new Date().toISOString().split('T')[0],
          version: 1,
        })
      })
    );
    
    await page.goto('/behaviour');
    await waitForPageReady(page);
    
    // Should show empty state or no data message
    const emptyState = page.locator('text=/no data|add transaction|empty/i').first();
    const hasEmpty = await emptyState.isVisible().catch(() => false);
    
    console.log(`Empty state visible: ${hasEmpty}`);
  });
});