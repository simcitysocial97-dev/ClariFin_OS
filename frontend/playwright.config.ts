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
  // redirects) and SPA routing only work under server mode.
  //
  // M9-C71 — port ownership. The servers are always started fresh in CI, where
  // the runner is exclusive. Locally, a previous run's orphaned `next start` or
  // uvicorn still holding :3000/:8000 aborted the whole run with
  // "http://localhost:8000/ready is already used" before a single assertion
  // ran — and because the orphans are invisible from the test process, the
  // failure looked like a configuration problem rather than a stale process.
  // `!process.env.CI` reuses a healthy local server and is the documented
  // Playwright pattern for exactly this; CI keeps exclusive ownership, so no
  // determinism is traded away where determinism is verifiable. The readiness
  // gates in `tests/global-setup.ts` then prove the reused server really does
  // serve every exercised route before the suite starts.
  webServer: [
    {
      command: 'npm start',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
      stdout: 'ignore',
      stderr: 'pipe',
    },
    {
      // Resolve Python via CLARIFIN_PYTHON env var (set by CI/bootstrap) or venv-first ladder.
      // No PYTHONPATH needed: -m uvicorn places cwd on sys.path[0], resolving `src.*`.
      command: 'cd ../backend && "${CLARIFIN_PYTHON:-$(if [ -x ../../.venv/bin/python ]; then echo ../../.venv/bin/python; else command -v python3 || command -v python; fi)}" -m uvicorn src.api:app --host 0.0.0.0 --port 8000',
      url: 'http://localhost:8000/ready',
      reuseExistingServer: !process.env.CI,
      timeout: 60000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
  
  // Output directory
  outputDir: 'test-results/artifacts',
});