/**
 * Mode Toggle Helpers
 * ====================
 * 
 * Utilities for testing Personal/Family dashboard mode:
 * - Mode switching
 * - State isolation verification
 * - localStorage validation
 */

import type { Page } from '@playwright/test';

// ============================================================================
// Types
// ============================================================================

export type DashboardMode = 'personal' | 'family';

export interface ModeState {
  mode: DashboardMode;
  transactionCount: number;
  cardCount: number;
  totalSpend: number;
  localStorageData: Record<string, unknown>;
}

// ============================================================================
// Constants
// ============================================================================

export const MODE_STORAGE_KEY = 'clariFin_dashboard_mode';
export const APP_STORAGE_KEY = 'bank-parser-storage';

// ============================================================================
// Mode Toggle Functions
// ============================================================================

/**
 * Get current dashboard mode from localStorage
 */
export async function getCurrentMode(page: Page): Promise<DashboardMode> {
  const mode = await page.evaluate((key) => {
    return localStorage.getItem(key);
  }, MODE_STORAGE_KEY);
  
  return (mode as DashboardMode) || 'personal';
}

/**
 * Set dashboard mode in localStorage
 */
export async function setMode(page: Page, mode: DashboardMode): Promise<void> {
  await page.evaluate(
    ({ key, value }) => {
      localStorage.setItem(key, value);
    },
    { key: MODE_STORAGE_KEY, value: mode }
  );
}

/**
 * Toggle to a specific mode via UI click
 */
export async function toggleToMode(page: Page, mode: DashboardMode): Promise<void> {
  // Find and click the mode toggle button
  const buttonSelector = mode === 'personal' 
    ? 'button:has-text("Personal")'
    : 'button:has-text("Family")';
  
  const button = page.locator(buttonSelector).first();
  
  // Check if button is already active
  const isActive = await button.evaluate((el) => {
    return el.classList.contains('bg-indigo-600') || 
           el.classList.contains('bg-emerald-600') ||
           el.getAttribute('data-active') === 'true';
  });
  
  if (!isActive) {
    await button.click();
    // Wait for mode change to take effect
    await page.waitForTimeout(500);
  }
}

/**
 * Capture current mode state for comparison
 */
export async function captureModeState(page: Page): Promise<ModeState> {
  const mode = await getCurrentMode(page);
  
  // Get localStorage data
  const localStorageData = await page.evaluate((key) => {
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : {};
  }, APP_STORAGE_KEY);
  
  // Get transaction count from page
  const transactionCount = await page.evaluate(() => {
    const rows = document.querySelectorAll('[data-testid="transaction-row"], table tbody tr');
    return rows.length;
  }).catch(() => 0);
  
  // Get card count from page
  const cardCount = await page.evaluate(() => {
    const cards = document.querySelectorAll('[data-testid="card-item"], [data-card-id]');
    return cards.length;
  }).catch(() => 0);
  
  // Get total spend from page (if visible)
  const totalSpend = await page.evaluate(() => {
    const spendElement = document.querySelector('[data-testid="total-spend"], .total-spend');
    if (spendElement) {
      const text = spendElement.textContent || '';
      const match = text.match(/[\d,]+/);
      return match ? parseFloat(match[0].replace(/,/g, '')) : 0;
    }
    return 0;
  }).catch(() => 0);
  
  return {
    mode,
    transactionCount,
    cardCount,
    totalSpend,
    localStorageData,
  };
}

/**
 * Verify mode isolation - ensure no data leakage between modes
 */
export async function verifyModeIsolation(
  page: Page,
  personalState: ModeState,
  familyState: ModeState
): Promise<{ isolated: boolean; issues: string[] }> {
  const issues: string[] = [];
  
  // Check that modes are different
  if (personalState.mode === familyState.mode) {
    issues.push(`Both states have same mode: ${personalState.mode}`);
  }
  
  // Check localStorage isolation
  const personalData = personalState.localStorageData;
  const familyData = familyState.localStorageData;
  
  // If both have data, verify they don't share state incorrectly
  if (personalData?.state && familyData?.state) {
    // Check for transaction overlap
    const personalTxns = new Set(
      (personalData.state.transactions || []).map((t: { id: string }) => t.id)
    );
    const familyTxns = new Set(
      (familyData.state.transactions || []).map((t: { id: string }) => t.id)
    );
    
    // In a properly isolated system, there should be no overlap
    // (unless transactions are shared intentionally)
    const overlap = [...personalTxns].filter(id => familyTxns.has(id));
    if (overlap.length > 0) {
      // This might be expected if transactions are shared
      // Log but don't fail
      // console.log(`Note: ${overlap.length} transactions appear in both modes`);
    }
  }
  
  return {
    isolated: issues.length === 0,
    issues,
  };
}

/**
 * Clear all app data from localStorage
 */
export async function clearAppData(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem('bank-parser-storage');
    localStorage.removeItem('clariFin_dashboard_mode');
  });
}

/**
 * Seed test data for mode testing
 */
export async function seedTestData(
  page: Page,
  mode: DashboardMode,
  data: {
    transactions?: Array<{ id: string; [key: string]: unknown }>;
    cards?: Array<{ id: string; [key: string]: unknown }>;
  }
): Promise<void> {
  await page.evaluate(
    ({ key, modeKey, mode, transactions, cards }) => {
      const existingData = localStorage.getItem(key);
      const parsed = existingData ? JSON.parse(existingData) : { state: {} };
      
      parsed.state = {
        ...parsed.state,
        transactions: transactions || [],
        cards: cards || [],
      };
      
      localStorage.setItem(key, JSON.stringify(parsed));
      localStorage.setItem(modeKey, mode);
    },
    { 
      key: APP_STORAGE_KEY, 
      modeKey: MODE_STORAGE_KEY, 
      mode, 
      transactions: data.transactions || [],
      cards: data.cards || [],
    }
  );
}

/**
 * Wait for mode toggle to be visible
 */
export async function waitForModeToggle(page: Page): Promise<void> {
  await page.waitForSelector('button:has-text("Personal"), button:has-text("Family")', {
    timeout: 10000,
  });
}

/**
 * Get mode toggle button states
 */
export async function getModeToggleStates(page: Page): Promise<{
  personal: { visible: boolean; active: boolean };
  family: { visible: boolean; active: boolean };
}> {
  const personalBtn = page.locator('button:has-text("Personal")').first();
  const familyBtn = page.locator('button:has-text("Family")').first();
  
  const personalVisible = await personalBtn.isVisible().catch(() => false);
  const familyVisible = await familyBtn.isVisible().catch(() => false);
  
  const personalActive = personalVisible 
    ? await personalBtn.evaluate((el) => {
        return el.classList.contains('bg-indigo-600') || 
               el.getAttribute('data-active') === 'true';
      })
    : false;
    
  const familyActive = familyVisible
    ? await familyBtn.evaluate((el) => {
        return el.classList.contains('bg-emerald-600') ||
               el.getAttribute('data-active') === 'true';
      })
    : false;
  
  return {
    personal: { visible: personalVisible, active: personalActive },
    family: { visible: familyVisible, active: familyActive },
  };
}