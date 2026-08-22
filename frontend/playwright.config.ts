/**
 * Playwright Test Configuration
 * ==============================
 * 
 * Production-grade configuration for ClariFin_OS testing:
 * - Multi-browser support
 * - Parallel execution
 * - Comprehensive reporting
 * - Global error capture
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Test directory
  testDir: './tests/e2e/specs',
  
  // Run tests in parallel
  fullyParallel: true,
  
  // Fail build on CI if test.only is left in
  forbidOnly: !!process.env.CI,
  
  // Retry failed tests on CI
  retries: process.env.CI ? 2 : 0,
  
  // M9-C8: run with bounded parallelism on CI. The matrix is sharded per
  // project (see .github/workflows/playwright.yml), so each CI job owns exactly
  // one project; parallelising the tests within that project keeps the per-job
  // runtime bounded well inside the job window instead of serialising all 232
  // tests (which previously blew past the timeout).
  workers: process.env.CI ? 4 : undefined,
  
  // Global timeout per test
  timeout: 30000,
  
  // Expect timeout
  expect: {
    timeout: 10000,
  },
  
  // Global setup
  globalSetup: './tests/global-setup.ts',
  
  // Reporters
  reporter: [
    ['html', { outputFolder: 'test-results/html-report', open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL
    baseURL: 'http://localhost:3000',
    
    // Collect trace on failure
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Action timeout
    actionTimeout: 15000,
    
    // Navigation timeout
    navigationTimeout: 30000,
  },
  
  // Configure projects for supported browsers only
  projects: [
    // Desktop Chrome (supported)
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
    },
    
    // Mobile Chrome (supported touch profile)
    {
      name: 'mobile-chrome',
      use: { 
        ...devices['Pixel 5'],
      },
    },
  ],
  
  // C38.6 — Deterministic E2E server lifecycle. The frontend is ALWAYS served
  // by `next start` (server mode), identical to local dev and production. We
  // never serve the static `dist` export because middleware (legacy-route
  // redirects) and SPA routing only work under server mode. `reuseExistingServer`
  // is intentionally FALSE so a test run can never depend on an accidentally
  // pre-existing server on :3000 — Playwright owns the lifecycle end to end.
  // The backend on :8000 is managed by Playwright to ensure deterministic startup.
  webServer: [
    {
      command: 'npm start',
      url: 'http://localhost:3000',
      reuseExistingServer: false,
      timeout: 120000,
      stdout: 'ignore',
      stderr: 'pipe',
    },
    {
      command: 'python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000',
      url: 'http://localhost:8000/ready',
      reuseExistingServer: false,
      timeout: 60000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
  
  // Output directory
  outputDir: 'test-results/artifacts',
});