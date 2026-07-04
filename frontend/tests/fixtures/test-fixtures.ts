/**
 * Custom Playwright Test Fixtures
 * ================================
 * 
 * Extends base test with:
 * - Console error capture
 * - Network error capture
 * - Hydration mismatch detection
 * - Performance metrics
 */

import { test as base, Page } from '@playwright/test';

// ============================================================================
// Types
// ============================================================================

export interface ConsoleMessage {
  type: 'error' | 'warning' | 'info' | 'debug';
  text: string;
  location?: string;
  timestamp: number;
}

export interface NetworkError {
  url: string;
  status: number;
  statusText: string;
  method: string;
  timestamp: number;
}

export interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
}

export interface ErrorCollector {
  consoleErrors: ConsoleMessage[];
  networkErrors: NetworkError[];
  hydrationErrors: string[];
  unhandledRejections: string[];
  performanceMetrics: PerformanceMetric[];
}

export interface TestFixtures {
  errorCollector: ErrorCollector;
  captureErrors: (page: Page) => void;
  assertNoErrors: () => void;
  waitForPageReady: (page: Page) => Promise<void>;
}

// ============================================================================
// Error Patterns to Detect
// ============================================================================

const HYDRATION_PATTERNS = [
  /Hydration failed/,
  /Text content does not match server-rendered HTML/,
  /There was an error while hydrating/,
  /Cannot read properties of null/,
  /Cannot read properties of undefined/,
  /Minified React error/,
];

const COMPILE_ERROR_PATTERNS = [
  /Failed to compile/,
  /Compile error/,
  /Module not found/,
  /Syntax error/,
];

const IGNORED_PATTERNS = [
  /favicon\.ico/, // Browser favicon requests
  /\.map$/, // Source maps
  /browser-parser\.js/, // External parser script
  /debug\.js/, // Debug script
  /\/api\//, // API calls (app has localStorage fallback)
  /localhost:8000/, // Backend API calls
  /_next\/static/, // Next.js static chunks (may 404 during build)
  /__nextjs_original-stack-frames/, // Next.js dev overlay
];

// Console error patterns to ignore (these are handled gracefully by the app)
const IGNORED_CONSOLE_PATTERNS = [
  /Failed to load resource.*404/, // Generic 404 resource errors (app has fallbacks)
  /Failed to load resource.*500/, // Server errors (app has fallbacks)
  /net::ERR_/, // Network errors (app has fallbacks)
];

// ============================================================================
// Fixtures
// ============================================================================

export const test = base.extend<TestFixtures>({
  // Error collector instance
  errorCollector: async ({}, use) => {
    const collector: ErrorCollector = {
      consoleErrors: [],
      networkErrors: [],
      hydrationErrors: [],
      unhandledRejections: [],
      performanceMetrics: [],
    };
    await use(collector);
  },

  // Setup error capture on page
  captureErrors: async ({ errorCollector }, use) => {
    const captureErrors = (page: Page) => {
      // Capture console messages
      page.on('console', (msg) => {
        const text = msg.text();
        const type = msg.type();
        const location = msg.location();
        
        // Ignore certain patterns (URL-based)
        if (IGNORED_PATTERNS.some(pattern => pattern.test(text))) {
          return;
        }
        
        // Ignore console error patterns (handled gracefully by app)
        if (IGNORED_CONSOLE_PATTERNS.some(pattern => pattern.test(text))) {
          return;
        }

        const message: ConsoleMessage = {
          type: type as ConsoleMessage['type'],
          text,
          location: location ? `${location.url}:${location.lineNumber}` : undefined,
          timestamp: Date.now(),
        };

        if (type === 'error') {
          errorCollector.consoleErrors.push(message);
          
          // Check for hydration errors
          if (HYDRATION_PATTERNS.some(pattern => pattern.test(text))) {
            errorCollector.hydrationErrors.push(text);
          }
          
          // Check for compile errors
          if (COMPILE_ERROR_PATTERNS.some(pattern => pattern.test(text))) {
            errorCollector.consoleErrors.push({
              ...message,
              text: `[COMPILE ERROR] ${text}`,
            });
          }
        }
      });

      // Capture page errors (unhandled exceptions)
      page.on('pageerror', (error) => {
        const message = error.message;
        
        // Check for hydration errors
        if (HYDRATION_PATTERNS.some(pattern => pattern.test(message))) {
          errorCollector.hydrationErrors.push(message);
        }
        
        errorCollector.consoleErrors.push({
          type: 'error',
          text: `[PAGE ERROR] ${message}`,
          timestamp: Date.now(),
        });
      });

      // Capture unhandled rejections via console
      page.on('console', (msg) => {
        if (msg.text().includes('Unhandled promise rejection')) {
          errorCollector.unhandledRejections.push(msg.text());
        }
      });

      // Capture network responses
      page.on('response', (response) => {
        const status = response.status();
        const url = response.url();
        
        // Ignore certain patterns
        if (IGNORED_PATTERNS.some(pattern => pattern.test(url))) {
          return;
        }

        // Capture error responses
        if (status >= 400) {
          errorCollector.networkErrors.push({
            url,
            status,
            statusText: response.statusText(),
            method: response.request().method(),
            timestamp: Date.now(),
          });
        }
      });
    };

    await use(captureErrors);
  },

  // Assert no errors were captured
  assertNoErrors: async ({ errorCollector }, use) => {
    const assertNoErrors = () => {
      const errors: string[] = [];

      // Check console errors
      if (errorCollector.consoleErrors.length > 0) {
        errors.push(`Console errors:\n${errorCollector.consoleErrors.map(e => `  - ${e.text}`).join('\n')}`);
      }

      // Check network errors
      if (errorCollector.networkErrors.length > 0) {
        errors.push(`Network errors:\n${errorCollector.networkErrors.map(e => `  - ${e.status} ${e.method} ${e.url}`).join('\n')}`);
      }

      // Check hydration errors
      if (errorCollector.hydrationErrors.length > 0) {
        errors.push(`Hydration errors:\n${errorCollector.hydrationErrors.map(e => `  - ${e}`).join('\n')}`);
      }

      // Check unhandled rejections
      if (errorCollector.unhandledRejections.length > 0) {
        errors.push(`Unhandled rejections:\n${errorCollector.unhandledRejections.map(e => `  - ${e}`).join('\n')}`);
      }

      if (errors.length > 0) {
        throw new Error(`Test failed with errors:\n\n${errors.join('\n\n')}`);
      }
    };

    await use(assertNoErrors);
  },

  // Wait for page to be fully ready
  waitForPageReady: async ({}, use) => {
    const waitForPageReady = async (page: Page) => {
      // Wait for network to be idle
      await page.waitForLoadState('networkidle');
      
      // Wait for React to hydrate
      await page.waitForFunction(() => {
        // Check if React has finished hydrating
        const root = document.getElementById('__next') || document.body;
        return root && root.children.length > 0;
      }, { timeout: 10000 });
      
      // Additional wait for any async rendering
      await page.waitForTimeout(500);
    };

    await use(waitForPageReady);
  },
});

// ============================================================================
// Exports
// ============================================================================

export { expect } from '@playwright/test';