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

  // Use system Python (dependencies already installed via bootstrap-runtime)
  const pythonCmd = 'python3';
  
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
      const pythonCmd = 'python3';
      
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
  }

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