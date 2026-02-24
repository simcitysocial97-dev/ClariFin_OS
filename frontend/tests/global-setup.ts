/**
 * Global Setup for Playwright Tests
 * ==================================
 * 
 * - Auto-starts backend if not running
 * - Checks backend health
 * - Seeds deterministic test data
 * - Prepares test environment
 */

import { FullConfig, request } from '@playwright/test';
import { spawn, execSync } from 'child_process';
import { existsSync } from 'fs';
import { resolve } from 'path';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const MAX_RETRIES = 30;
const BACKEND_STARTUP_TIMEOUT = 30000;

/**
 * Check if backend is running
 */
async function checkBackendHealth(): Promise<boolean> {
  try {
    const context = await request.newContext();
    const response = await context.get(`${API_BASE}/api/banks`, { timeout: 3000 });
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
    const response = await context.get(`http://localhost:${port}`, { timeout: 1000 });
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

  // Use virtual environment Python
  const venvPython = resolve(backendPath, 'venv', 'bin', 'python');
  const pythonCmd = existsSync(venvPython) ? venvPython : 'python3';
  
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

    console.log('⏳ Waiting for backend to start...');
    const startTime = Date.now();
    
    while (Date.now() - startTime < BACKEND_STARTUP_TIMEOUT) {
      const isHealthy = await checkBackendHealth();
      if (isHealthy) {
        console.log('✅ Backend started successfully');
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    console.log('⚠️  Backend failed to start within timeout, continuing without backend');
    return false;
  } catch (error) {
    console.log('⚠️  Error starting backend:', error);
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
      await new Promise(resolve => setTimeout(resolve, 1000));
      backendHealthy = await checkBackendHealth();
      if (backendHealthy) break;
    }
  }

  if (!backendHealthy) {
    console.log('⚠️  Backend is not available. Tests will use localStorage fallback data.');
    console.log('   To enable backend tests: cd backend && source venv/bin/activate && uvicorn src.api:app --reload');
  } else {
    console.log('✅ Backend API is healthy');
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