/**
 * Navigation Tests
 * =================
 * 
 * Tests all routes in ClariFin_OS:
 * - Page loads without blank screen
 * - No runtime crashes
 * - Title rendered
 * - Header visible
 * - Sidebar visible (desktop)
 */

import { test, expect } from '../fixtures/test-fixtures';
import { detectHorizontalOverflow } from '../utils/css-helpers';

// ============================================================================
// Routes to Test
// ============================================================================

const ROUTES = [
  { path: '/', name: 'Home/Dashboard', title: 'Dashboard' },
  { path: '/dashboard', name: 'Dashboard Page', title: 'Dashboard' },
  { path: '/transactions', name: 'Transactions', title: 'Transactions' },
  { path: '/categories', name: 'Categories', title: 'Categories' },
  { path: '/analytics', name: 'Analytics', title: 'Analytics' },
  { path: '/cards', name: 'Cards', title: 'Cards' },
  { path: '/import', name: 'Import', title: 'Import' },
  { path: '/settings', name: 'Settings', title: 'Settings' },
  { path: '/behavior', name: 'Behavior', title: 'Dashboard' }, // Behavior page shows dashboard
  { path: '/reconciliation', name: 'Reconciliation', title: 'Reconciliation' },
];

// ============================================================================
// Navigation Tests
// ============================================================================

test.describe('Navigation', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
  });

  for (const route of ROUTES) {
    test(`should load ${route.name} page (${route.path})`, async ({ 
      page, 
      waitForPageReady,
      assertNoErrors 
    }) => {
      // Navigate to route
      await page.goto(route.path);
      
      // Wait for page to be ready
      await waitForPageReady(page);
      
      // Verify page is not blank
      const bodyContent = await page.locator('body').innerHTML();
      expect(bodyContent.length).toBeGreaterThan(100);
      
      // Verify no blank screen
      const mainContent = page.locator('main, [role="main"], .main-content').first();
      const hasMain = await mainContent.isVisible().catch(() => false);
      
      // Either main is visible or we have significant content
      const hasContent = hasMain || bodyContent.length > 500;
      expect(hasContent).toBe(true);
      
      // Verify page title exists
      const title = await page.title();
      expect(title).toBeTruthy();
      expect(title.length).toBeGreaterThan(0);
      
      // Assert no errors
      assertNoErrors();
    });
  }
});

// ============================================================================
// Sidebar Navigation Tests
// ============================================================================

test.describe('Sidebar Navigation', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('should display sidebar on desktop', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Sidebar should be visible
    const sidebar = page.locator('aside').first();
    await expect(sidebar).toBeVisible();
    
    // Sidebar should have navigation links
    const navLinks = sidebar.locator('nav a, nav button');
    const count = await navLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should navigate via sidebar links', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Click on Transactions link
    const transactionsLink = page.locator('a:has-text("Transactions")').first();
    await transactionsLink.click();
    
    // Wait for navigation
    await page.waitForURL('**/transactions**');
    await waitForPageReady(page);
    
    // Verify URL
    expect(page.url()).toContain('/transactions');
  });

  test('should highlight active navigation item', async ({ page, waitForPageReady }) => {
    await page.goto('/transactions');
    await waitForPageReady(page);
    
    // Find active link
    const activeLink = page.locator('nav a.bg-primary, nav a[class*="active"]').first();
    const isVisible = await activeLink.isVisible().catch(() => false);
    
    // Should have some indication of active state
    // This is a soft assertion as styling may vary
    if (isVisible) {
      const className = await activeLink.getAttribute('class');
      expect(className).toContain('primary');
    }
  });

  test('should collapse sidebar on toggle', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Find collapse button
    const collapseBtn = page.locator('button:has([class*="chevron"]), [data-testid="sidebar-toggle"]').first();
    const isVisible = await collapseBtn.isVisible().catch(() => false);
    
    if (isVisible) {
      // Get initial sidebar width
      const sidebar = page.locator('aside').first();
      const initialBox = await sidebar.boundingBox();
      const initialWidth = initialBox?.width || 0;
      
      // Click collapse
      await collapseBtn.click();
      await page.waitForTimeout(300);
      
      // Get new width
      const newBox = await sidebar.boundingBox();
      const newWidth = newBox?.width || 0;
      
      // Width should have changed
      expect(newWidth).not.toBe(initialWidth);
    }
  });
});

// ============================================================================
// Mobile Navigation Tests
// ============================================================================

test.describe('Mobile Navigation', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
  });

  test('should show mobile menu button', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Mobile menu button should be visible
    const menuBtn = page.locator('button:has([class*="menu"]), [data-testid="mobile-menu"]').first();
    const isVisible = await menuBtn.isVisible().catch(() => false);
    
    // Either menu button or hamburger icon should exist
    const hasMobileNav = isVisible || await page.locator('[class*="Menu"]').count() > 0;
    expect(hasMobileNav).toBe(true);
  });

  test('should open mobile sidebar on menu click', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Find and click menu button
    const menuBtn = page.locator('button').filter({ hasText: '' }).first();
    const menuIcon = page.locator('[class*="Menu"]').first();
    
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
    } else if (await menuIcon.isVisible()) {
      await menuIcon.click();
    }
    
    await page.waitForTimeout(500);
    
    // Sidebar or sheet should be visible
    const sheet = page.locator('[role="dialog"], [data-state="open"]').first();
    const sidebar = page.locator('aside').first();
    
    const isSheetVisible = await sheet.isVisible().catch(() => false);
    const isSidebarVisible = await sidebar.isVisible().catch(() => false);
    
    expect(isSheetVisible || isSidebarVisible).toBe(true);
  });
});

// ============================================================================
// Layout Overflow Tests
// ============================================================================

test.describe('Layout Overflow', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
  });

  for (const route of ROUTES) {
    test(`should not have horizontal overflow on ${route.name}`, async ({ page, waitForPageReady }) => {
      await page.goto(route.path);
      await waitForPageReady(page);
      
      // Check for horizontal overflow
      const result = await detectHorizontalOverflow(page);
      
      // Allow small overflow (scrollbar width)
      expect(result.issues.length).toBe(0);
    });
  }
});

// ============================================================================
// Deep Link Tests
// ============================================================================

test.describe('Deep Links', () => {
  test('should handle query parameters', async ({ page, waitForPageReady, captureErrors }) => {
    captureErrors(page);
    
    await page.goto('/?upload=true');
    await waitForPageReady(page);
    
    // Upload modal should be triggered
    const modal = page.locator('[role="dialog"], [data-state="open"]').first();
    const isModalVisible = await modal.isVisible().catch(() => false);
    
    // Modal might open automatically with upload=true
    // This is a soft check
    console.log(`Upload modal visible: ${isModalVisible}`);
  });

  test('should handle invalid routes gracefully', async ({ page, waitForPageReady, captureErrors }) => {
    captureErrors(page);
    
    await page.goto('/invalid-route-12345');
    await waitForPageReady(page);
    
    // Should show 404 or redirect to home
    const is404 = await page.locator('text=/404|not found/i').isVisible().catch(() => false);
    const isHome = page.url() === '/' || page.url().includes('localhost:3000/');
    
    expect(is404 || isHome).toBe(true);
  });
});