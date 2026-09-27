/**
 * Global Setup for Playwright Tests
 * ==================================
 * 
 * - Auto-starts backend if not running
 * - Checks backend health
 * - Seeds deterministic test data
 * - Prepares test environment
 */

import type { FullConfig } from '@playwright/test';
import { request } from '@playwright/test';
import { spawn } from 'child_process';
import { existsSync } from 'fs';
import { resolve } from 'path';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const MAX_RETRIES = 30;
const BACKEND_STARTUP_TIMEOUT = process.env.CI ? 120000 : 30000;
const HEALTH_CHECK_RETRY_DELAY = 1000;
const HEALTH_CHECK_ENDPOINT = `${API_BASE}/ready`;

/**
 * Resolve the canonical Python interpreter.
 * Priority: CLARIFIN_PYTHON env var > repo-root .venv/bin/python > python3 from PATH
 */
function resolvePython(): string {
  // Check for explicit override (set by CI/local bootstrap)
  if (process.env.CLARIFIN_PYTHON) {
    return process.env.CLARIFIN_PYTHON;
  }
  // Repo root is two levels up from frontend/tests/
  const repoRoot = resolve(process.cwd(), '..', '..');
  const venvPython = resolve(repoRoot, '.venv', 'bin', 'python');
  if (existsSync(venvPython)) {
    return venvPython;
  }
  // Fallback to PATH python3
  return 'python3';
}

/**
 * Check if backend is running using the /ready endpoint
 */
async function checkBackendHealth(): Promise<boolean> {
  try {
    const context = await request.newContext();
    const response = await context.get(HEALTH_CHECK_ENDPOINT, { timeout: 3000 });
    await context.dispose();
    return response.ok();
  } catch {
    return false;
  }
}

/**
 * Check if port is in use
 */
async function isPortInUse(port: number): Promise<boolean> {
  try {
    const context = await request.newContext();
    const _response = await context.get(`http://localhost:${port}`, { timeout: 1000 });
    await context.dispose();
    return true;
  } catch {
    return false;
  }
}

/**
 * Start FastAPI backend server using virtual environment
 */
async function startBackend(): Promise<boolean> {
  console.log('🔧 Starting FastAPI backend...');
  
  const backendPath = resolve(process.cwd(), '..', 'backend');
  if (!existsSync(backendPath)) {
    console.log('⚠️  Backend directory not found at:', backendPath);
    return false;
  }

  const pythonCmd = resolvePython();
  console.log(`Using Python: ${pythonCmd}`);

  try {
    // Use src.api:app as the entry point (src/api.py contains the FastAPI app)
    const backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'src.api:app', '--host', '0.0.0.0', '--port', '8000'], {
      cwd: backendPath,
      stdio: 'pipe',
      detached: false,
    });

    backendProcess.stdout?.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr?.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`);
    });

    backendProcess.on('error', (error) => {
      console.log('⚠️  Failed to start backend process:', error.message);
    });

    backendProcess.on('exit', (code) => {
      console.log(`⚠️  Backend process exited with code ${code}`);
    });

    console.log('⏳ Waiting for backend to start...');
    const startTime = Date.now();
    let retryCount = 0;
    
    while (Date.now() - startTime < BACKEND_STARTUP_TIMEOUT) {
      const isHealthy = await checkBackendHealth();
      if (isHealthy) {
        console.log('✅ Backend started successfully');
        return true;
      }
      retryCount++;
      const retryDelay = HEALTH_CHECK_RETRY_DELAY * Math.pow(2, retryCount); // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }

    console.log('❌ Backend failed to start within timeout');
    return false;
  } catch (error) {
    console.log('⚠️  Error starting backend:', error);
    return false;
  }
}

/**
 * Seed deterministic test data into the backend SQLite database
 */
async function seedTestData(): Promise<boolean> {
  try {
    const { spawn } = await import('child_process');
    const { resolve } = await import('path');
    const { existsSync } = await import('fs');
    
    const backendPath = resolve(process.cwd(), '..', 'backend');
    const dbPath = resolve(backendPath, 'data', 'finance.db');
    
    if (!existsSync(dbPath)) {
      console.log('⚠️  Database not found at:', dbPath);
      return false;
    }
    
    const seedScript = `
import sqlite3
import os

db_path = '${dbPath}'
seed_sql = """
CREATE TABLE IF NOT EXISTS banks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    metadata TEXT
);

INSERT OR IGNORE INTO banks (name) VALUES ('Test Bank');

INSERT OR IGNORE INTO accounts (id, name, bank, account_type, balance_paise, account_number_last4)
VALUES (1, 'Primary Checking', 'Test Bank', 'savings', 500000, '1234'),
       (2, 'Savings', 'Test Bank', 'savings', 1000000, '5678');

INSERT OR REPLACE INTO statements (id, bank, file_name, statement_period_from, statement_period_to)
VALUES (1, 'Test Bank', 'test.csv', '2025-01-01', '2025-01-31');

INSERT OR IGNORE INTO transactions
    (statement_id, date, date_iso, description, amount_paise, type, account_id)
VALUES (1, '01/01/2025', '2025-01-01', 'Test Transaction 1', 100000, 'debit', 1),
       (1, '02/01/2025', '2025-02-01', 'Test Transaction 2', 50000, 'credit', 1),
       (1, '03/01/2025', '2025-03-01', 'Test Transaction 3', 75000, 'debit', 2);
""";

conn = sqlite3.connect(db_path)
conn.executescript(seed_sql)
conn.commit()
conn.close()
print(f'Seeded {db_path}')
`;
    
    return new Promise((resolve) => {
      const pythonCmd = resolvePython();
      
      const proc = spawn(pythonCmd, ['-c', seedScript], { cwd: backendPath });
      let stdout = '';
      let stderr = '';
      
      proc.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      proc.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      proc.on('close', (code) => {
        if (code === 0) {
          console.log('✅ Test data seeded successfully');
          resolve(true);
        } else {
          console.log('⚠️  Seeding failed:', stderr);
          resolve(false);
        }
      });
    });
  } catch (error) {
    console.log('⚠️  Error seeding test data:', error);
    return false;
  }
}

/**
 * Warm the Platform Console's data path before the suite starts.
 *
 * M9-C71. The console mounts six queries on its dashboard (health, events,
 * error count, open obligations, capabilities, members). On a cold process the
 * first platform call pays framework/architecture materialisation, so the very
 * first `waitUntil: 'networkidle'` navigation to /platform took 26.1 s of a 30 s
 * budget and the rest of the suite tipped over it. That is a property of a
 * freshly spawned backend, not of the console, and it made every platform test
 * a coin flip.
 *
 * Readiness is therefore part of environment setup: touch every platform
 * endpoint the console actually calls, wait for each to answer, and report the
 * cost. No assertion is affected — this only defines the state the suite starts
 * from, the same way the existing /ready + seeding steps already do.
 */
const PLATFORM_WARMUP_ENDPOINTS = [
  '/platform/v1/health',
  '/platform/v1/capabilities',
  '/platform/v1/events?limit=8',
  '/platform/v1/errors/current',
  '/platform/v1/tasks',
  '/platform/v1/workflows',
  '/platform/v1/runs',
  '/api/v1/members',
];

const PLATFORM_WARMUP_BUDGET_MS = Number(
  process.env.PLAYWRIGHT_PLATFORM_WARMUP_BUDGET_MS || 120000,
);

async function warmPlatformApi(): Promise<boolean> {
  console.log('♨️  Warming the Platform Console data path...');
  const deadline = Date.now() + PLATFORM_WARMUP_BUDGET_MS;
  const context = await request.newContext();
  const pending = new Set(PLATFORM_WARMUP_ENDPOINTS);
  let complete = false;

  try {
    while (pending.size > 0 && Date.now() < deadline) {
      for (const endpoint of [...pending]) {
        const started = Date.now();
        try {
          const response = await context.get(`${API_BASE}${endpoint}`, { timeout: 30000 });
          if (response.ok()) {
            pending.delete(endpoint);
            console.log(`   warm ${endpoint} -> ${response.status()} in ${Date.now() - started}ms`);
          }
        } catch {
          // Endpoint still starting; retried on the next pass.
        }
      }
      if (pending.size === 0) break;
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    complete = pending.size === 0;
  } finally {
    await context.dispose();
  }

  if (complete) {
    console.log('✅ Platform Console data path is warm');
  } else {
    console.log(
      `⚠️  Platform warmup incomplete within ${PLATFORM_WARMUP_BUDGET_MS}ms; ` +
        `still pending: ${[...pending].join(', ')}`,
    );
  }
  return complete;
}

/**
 * Prove the frontend actually serves the routes the suite exercises, before the
 * first test navigates.
 *
 * M9-C71. `webServer.url` only proves that *something* answers on :3000. On a
 * cold `next start` the server accepts connections before its route table is
 * fully materialised, so the first navigations intermittently received the
 * not-found page: identical specs returned 200 on one run and a Next.js "This
 * page could not be found." on the next with no code change in between. All
 * eight console routes were verified to return 200 with the console title bar
 * once the server was warm.
 *
 * This is a readiness gate, exactly like the existing /ready probe and the
 * platform API warmup: it defines the state the suite starts from. No
 * assertion, threshold or wait in any spec is changed.
 */
const FRONTEND_BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
/**
 * Every route the suite navigates to, each with the shell marker that proves
 * the route was actually served by the application rather than answered by the
 * not-found page. A single global marker does not work: the financial shell
 * and the Platform Console are different applications (the console deliberately
 * renders no financial AppShell), so each route family has its own marker.
 */
const CONSOLE_SHELL_MARKER = 'data-testid="platform-title-bar"';
const FINANCIAL_SHELL_MARKER = 'data-testid="app-shell"';

const FRONTEND_ROUTES: ReadonlyArray<readonly [string, string]> = [
  ['/dashboard/', FINANCIAL_SHELL_MARKER],
  ['/transactions/', FINANCIAL_SHELL_MARKER],
  ['/platform/', CONSOLE_SHELL_MARKER],
  ['/platform/health/', CONSOLE_SHELL_MARKER],
  ['/platform/verification/', CONSOLE_SHELL_MARKER],
  ['/platform/diagnostics/', CONSOLE_SHELL_MARKER],
  ['/platform/workflows/', CONSOLE_SHELL_MARKER],
  ['/platform/capabilities/', CONSOLE_SHELL_MARKER],
  ['/platform/runs/', CONSOLE_SHELL_MARKER],
  ['/platform/evidence/', CONSOLE_SHELL_MARKER],
];
const FRONTEND_WARMUP_BUDGET_MS = Number(process.env.PLAYWRIGHT_FRONTEND_WARMUP_BUDGET_MS || 90000);

async function warmFrontend(): Promise<boolean> {
  console.log('♨️  Waiting for the frontend to serve every exercised route...');
  const deadline = Date.now() + FRONTEND_WARMUP_BUDGET_MS;
  const pending = new Map(FRONTEND_ROUTES);
  const context = await request.newContext();
  let complete = false;
  try {
    while (pending.size > 0 && Date.now() < deadline) {
      for (const [route, marker] of [...pending]) {
        try {
          const response = await context.get(`${FRONTEND_BASE}${route}`, { timeout: 15000 });
          const body = await response.text();
          // Positive check on the route family's own shell marker. A negative
          // check on the not-found copy is NOT usable: a correctly rendered page
          // also embeds that string (the root layout ships the not-found
          // template), so a negative test never passes.
          if (response.ok() && body.includes(marker)) {
            pending.delete(route);
          }
        } catch {
          // Server still warming; retried on the next pass.
        }
      }
      if (pending.size === 0) break;
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    complete = pending.size === 0;
  } finally {
    await context.dispose();
  }
  if (complete) {
    console.log('✅ Frontend serves every exercised route');
  } else {
    // Fail fast rather than continue. On a cold `next start` the server
    // intermittently answers the first navigations with the not-found page, and
    // continuing produced a storm of 30 s `waitForSelector` timeouts that all
    // looked like application failures. A missing route is an environment
    // problem and must say so.
    console.log(
      `❌ Frontend did not serve every exercised route within ` +
        `${FRONTEND_WARMUP_BUDGET_MS}ms; still missing the console shell on: ` +
        `${[...pending].join(', ')}`,
    );
    throw new Error(
      `Frontend route warmup incomplete. Routes without their shell marker: ` +
        `${[...pending].map(([route, marker]) => `${route} (${marker})`).join(', ')}. ` +
        `This is an environment/readiness failure, not an application failure.`,
    );
  }
  return complete;
}

async function globalSetup(config: FullConfig) {
  console.log('🔧 Running global setup...');

  // Check if backend port is available
  const portInUse = await isPortInUse(8000);
  
  if (!portInUse) {
    console.log('🔌 Port 8000 is available, starting backend...');
    await startBackend();
  } else {
    console.log('🔌 Port 8000 is in use, checking health...');
  }

  // Verify backend health
  let backendHealthy = await checkBackendHealth();
  
  if (!backendHealthy) {
    console.log('⚠️  Backend not responding. Retrying...');
    for (let i = 0; i < MAX_RETRIES; i++) {
      await new Promise(resolve => setTimeout(resolve, HEALTH_CHECK_RETRY_DELAY));
      backendHealthy = await checkBackendHealth();
      if (backendHealthy) break;
    }
  }

  if (!backendHealthy) {
    console.log('❌ Backend is not available. Failing fast.');
    process.exit(1); // Fail fast if backend is not available
  } else {
    console.log('✅ Backend API is healthy');
    
    // Seed deterministic test data
    await seedTestData();

    // M9-C71: bring the platform console's data path up before any assertion
    // runs, so a cold backend is not charged to the first test.
    await warmPlatformApi();
  }

  // M9-C71: the frontend must actually serve every route the suite exercises
  // before the first test navigates.
  await warmFrontend();

  // Store setup status
  const setupData = {
    backendAvailable: true,
    setupTime: new Date().toISOString(),
  };

  const fs = await import('fs');
  const path = await import('path');
  const setupPath = path.join(__dirname, '../test-results/.setup-status.json');
  
  const dir = path.dirname(setupPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  fs.writeFileSync(setupPath, JSON.stringify(setupData, null, 2));
  console.log('✅ Global setup complete');
}

export default globalSetup;