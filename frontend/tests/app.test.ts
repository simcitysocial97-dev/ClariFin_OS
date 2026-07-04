import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Bank Statement Parser App', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('should load dashboard page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('text=Welcome back')).toBeVisible();
  });

  test('should show upload zone when no cards', async ({ page }) => {
    // Clear localStorage first
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    
    // Use more specific selector for the main upload button
    await expect(page.locator('main').locator('button:has-text("Upload Statement")')).toBeVisible();
  });

  test('should upload and parse PDF', async ({ page }) => {
    // Clear localStorage first to ensure clean state
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    
    // Wait for empty state to be visible
    await expect(page.locator('text=Welcome to Bank Statement Parser')).toBeVisible();
    
    // Click the upload button to open the modal
    await page.click('button:has-text("Upload Your First Statement")');
    await page.waitForTimeout(500);
    
    // Upload test PDF - use the hidden file input in the modal
    const pdfPath = path.join(__dirname, '../../test/statements/icici_feb.pdf');
    
    // Find the file input in the modal (it's hidden but accessible)
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(pdfPath);
    
    // Wait for parsing to complete (check localStorage)
    await page.waitForFunction(() => {
      const data = localStorage.getItem('bank-parser-storage');
      if (!data) return false;
      const parsed = JSON.parse(data);
      return parsed.state?.transactions?.length > 0;
    }, { timeout: 30000 });
    
    // Verify data was stored
    const storedData = await page.evaluate(() => {
      const data = localStorage.getItem('bank-parser-storage');
      return data ? JSON.parse(data) : null;
    });
    
    expect(storedData.state.transactions.length).toBeGreaterThan(0);
    expect(storedData.state.cards.length).toBeGreaterThan(0);
    
    console.log('Parsed:', {
      transactions: storedData.state.transactions.length,
      cards: storedData.state.cards.length
    });
  });

  test('should display correct metadata', async ({ page }) => {
    // Clear localStorage first to ensure clean state
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    
    const pdfPath = path.join(__dirname, '../../test/statements/icici_feb.pdf');
    
    // Click the upload button to open the modal
    await page.click('button:has-text("Upload Your First Statement")');
    await page.waitForTimeout(500);
    
    // Upload file
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(pdfPath);
    
    // Wait for parsing with longer timeout
    await page.waitForFunction(() => {
      const data = localStorage.getItem('bank-parser-storage');
      if (!data) return false;
      const parsed = JSON.parse(data);
      return parsed.state?.cards?.length > 0;
    }, { timeout: 30000 });
    
    // Check metadata values
    const storedData = await page.evaluate(() => {
      const data = localStorage.getItem('bank-parser-storage');
      return data ? JSON.parse(data) : null;
    });
    
    const card = storedData.state.cards[0];
    
    // Verify metadata matches expected values for icici_feb.pdf
    expect(card.bankName).toBe('ICICI Bank');
    expect(card.totalAmountDue).toBeGreaterThan(0);
    expect(card.cardNumber).toBeTruthy(); // Should have some card number
  });

  test('should navigate between pages', async ({ page }) => {
    // Test navigation
    const navLinks = ['Transactions', 'Analytics', 'Cards', 'Settings'];
    
    for (const linkText of navLinks) {
      const link = page.locator(`a:has-text("${linkText}"), button:has-text("${linkText}")`).first();
      if (await link.isVisible()) {
        await link.click();
        await page.waitForLoadState('networkidle');
      }
    }
  });

  test('should filter and clear filter', async ({ page }) => {
    // Clear localStorage first to ensure clean state
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    
    const pdfPath = path.join(__dirname, '../../test/statements/icici_feb.pdf');
    
    // Click the upload button to open the modal
    await page.click('button:has-text("Upload Your First Statement")');
    await page.waitForTimeout(500);
    
    // Upload file
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(pdfPath);
    
    // Wait for parsing with longer timeout
    await page.waitForFunction(() => {
      const data = localStorage.getItem('bank-parser-storage');
      if (!data) return false;
      const parsed = JSON.parse(data);
      return parsed.state?.cards?.length > 0;
    }, { timeout: 30000 });
    
    // Go to cards page
    await page.click('a:has-text("Cards")');
    await page.waitForLoadState('networkidle');
    
    // Click view on card (if button exists)
    const viewBtn = page.locator('button:has-text("View")').first();
    if (await viewBtn.isVisible()) {
      await viewBtn.click();
      await page.waitForTimeout(1000);
      
      // Find and click clear filter button on transactions page
      const clearBtn = page.locator('button:has-text("Clear Filter")').first();
      if (await clearBtn.isVisible()) {
        await clearBtn.click();
        await page.waitForTimeout(500);
        
        // Verify filter was cleared
        const storedData = await page.evaluate(() => {
          const data = localStorage.getItem('bank-parser-storage');
          return data ? JSON.parse(data) : null;
        });
        
        expect(storedData.state.selectedCardId).toBeNull();
      }
    }
  });
});
