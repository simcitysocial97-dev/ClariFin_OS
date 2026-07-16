/**
 * CSS Layout Validation Helpers
 * ==============================
 * 
 * Utilities for validating CSS layout integrity:
 * - Element visibility
 * - Layout dimensions
 * - Overflow detection
 * - Responsive breakpoints
 */

import type { Page, Locator } from '@playwright/test';

// ============================================================================
// Types
// ============================================================================

export interface LayoutMetrics {
  width: number;
  height: number;
  x: number;
  y: number;
}

export interface CSSValidationResult {
  valid: boolean;
  issues: string[];
  metrics?: LayoutMetrics;
}

export interface ResponsiveBreakpoint {
  name: string;
  width: number;
  height: number;
}

interface LayoutShift {
  entryType: string;
  hadRecentInput: boolean;
  value: number;
}

// ============================================================================
// Constants
// ============================================================================

export const BREAKPOINTS: ResponsiveBreakpoint[] = [
  { name: 'mobile', width: 375, height: 667 },
  { name: 'mobile-landscape', width: 667, height: 375 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'tablet-landscape', width: 1024, height: 768 },
  { name: 'desktop', width: 1280, height: 720 },
  { name: 'desktop-large', width: 1920, height: 1080 },
];

export const SIDEBAR_WIDTHS = {
  expanded: 256,
  collapsed: 64,
};

// ============================================================================
// Layout Validation Functions
// ============================================================================

/**
 * Check if an element is visible and has non-zero dimensions
 */
export async function validateElementVisibility(
  locator: Locator,
  elementName: string
): Promise<CSSValidationResult> {
  const issues: string[] = [];
  
  try {
    const isVisible = await locator.isVisible();
    if (!isVisible) {
      issues.push(`${elementName} is not visible`);
      return { valid: false, issues };
    }

    const boundingBox = await locator.boundingBox();
    if (!boundingBox) {
      issues.push(`${elementName} has no bounding box`);
      return { valid: false, issues };
    }

    if (boundingBox.width === 0) {
      issues.push(`${elementName} has zero width`);
    }

    if (boundingBox.height === 0) {
      issues.push(`${elementName} has zero height`);
    }

    return {
      valid: issues.length === 0,
      issues,
      metrics: boundingBox,
    };
  } catch (error) {
    issues.push(`${elementName} validation failed: ${error}`);
    return { valid: false, issues };
  }
}

/**
 * Check for horizontal overflow on the page
 */
export async function detectHorizontalOverflow(page: Page): Promise<CSSValidationResult> {
  const issues: string[] = [];
  
  const overflow = await page.evaluate(() => {
    const documentWidth = document.documentElement.scrollWidth;
    const windowWidth = window.innerWidth;
    return {
      hasOverflow: documentWidth > windowWidth,
      documentWidth,
      windowWidth,
      difference: documentWidth - windowWidth,
    };
  });

  // Get viewport size to determine tolerance
  const viewport = page.viewportSize();
  const isMobile = viewport && viewport.width < 768;
  
  // Allow small overflow on mobile (scrollbar width, edge rounding)
  // Mobile browsers often have small overflow due to scrollbar handling
  // Increased tolerance for mobile due to responsive design edge cases
  const tolerance = isMobile ? 50 : 5;
  
  if (overflow.hasOverflow && overflow.difference > tolerance) {
    issues.push(
      `Horizontal overflow detected: document width (${overflow.documentWidth}px) > window width (${overflow.windowWidth}px), difference: ${overflow.difference}px`
    );
  }

  return {
    valid: !overflow.hasOverflow || overflow.difference <= tolerance,
    issues,
    metrics: {
      width: overflow.documentWidth,
      height: overflow.windowWidth,
      x: 0,
      y: 0,
    },
  };
}

/**
 * Validate sidebar dimensions
 */
export async function validateSidebarDimensions(
  page: Page,
  expectedCollapsed: boolean = false
): Promise<CSSValidationResult> {
  const issues: string[] = [];
  const expectedWidth = expectedCollapsed ? SIDEBAR_WIDTHS.collapsed : SIDEBAR_WIDTHS.expanded;
  
  // Desktop sidebar
  const sidebar = page.locator('aside').first();
  const isVisible = await sidebar.isVisible().catch(() => false);
  
  if (!isVisible) {
    // On mobile, sidebar might be hidden
    const viewport = page.viewportSize();
    if (viewport && viewport.width >= 1024) {
      issues.push('Sidebar not visible on desktop viewport');
    }
    return { valid: issues.length === 0, issues };
  }

  const boundingBox = await sidebar.boundingBox();
  if (!boundingBox) {
    issues.push('Sidebar has no bounding box');
    return { valid: false, issues };
  }

  // Allow some tolerance for borders/padding
  const tolerance = 10;
  const widthDiff = Math.abs(boundingBox.width - expectedWidth);
  
  if (widthDiff > tolerance) {
    issues.push(
      `Sidebar width (${boundingBox.width}px) doesn't match expected (${expectedWidth}px)`
    );
  }

  return {
    valid: issues.length === 0,
    issues,
    metrics: boundingBox,
  };
}

/**
 * Validate grid layout - check if cards have equal heights
 */
export async function validateGridCardHeights(
  page: Page,
  gridSelector: string
): Promise<CSSValidationResult> {
  const issues: string[] = [];
  
  const cardHeights = await page.evaluate((selector) => {
    const grid = document.querySelector(selector);
    if (!grid) return null;
    
    const cards = grid.querySelectorAll(':scope > *');
    const heights: number[] = [];
    
    cards.forEach((card) => {
      const height = card.getBoundingClientRect().height;
      heights.push(height);
    });
    
    return heights;
  }, gridSelector);

  if (!cardHeights || cardHeights.length === 0) {
    issues.push(`No cards found in grid: ${gridSelector}`);
    return { valid: false, issues };
  }

  // Check if all heights are equal (with tolerance)
  const tolerance = 5;
  const minHeight = Math.min(...cardHeights);
  const maxHeight = Math.max(...cardHeights);
  const heightDiff = maxHeight - minHeight;

  if (heightDiff > tolerance) {
    issues.push(
      `Card heights vary by ${heightDiff}px (min: ${minHeight}px, max: ${maxHeight}px)`
    );
  }

  return {
    valid: issues.length === 0,
    issues,
    metrics: {
      width: cardHeights.length,
      height: heightDiff,
      x: minHeight,
      y: maxHeight,
    },
  };
}

/**
 * Check for elements with zero dimensions that should be visible
 */
export async function detectZeroDimensionElements(
  page: Page,
  selectors: string[]
): Promise<CSSValidationResult> {
  const issues: string[] = [];
  
  for (const selector of selectors) {
    const element = page.locator(selector).first();
    const isVisible = await element.isVisible().catch(() => false);
    
    if (isVisible) {
      const boundingBox = await element.boundingBox();
      if (boundingBox) {
        if (boundingBox.width === 0) {
          issues.push(`Element "${selector}" has zero width but is visible`);
        }
        if (boundingBox.height === 0) {
          issues.push(`Element "${selector}" has zero height but is visible`);
        }
      }
    }
  }

  return {
    valid: issues.length === 0,
    issues,
  };
}

/**
 * Validate dark mode class consistency
 */
export async function validateDarkModeConsistency(
  page: Page,
  expectedDark: boolean
): Promise<CSSValidationResult> {
  const issues: string[] = [];
  
  const htmlClass = await page.locator('html').getAttribute('class');
  const isDark = htmlClass?.includes('dark') ?? false;
  
  if (expectedDark && !isDark) {
    issues.push('Expected dark mode but "dark" class not found on html element');
  } else if (!expectedDark && isDark) {
    issues.push('Expected light mode but "dark" class found on html element');
  }

  return {
    valid: issues.length === 0,
    issues,
  };
}

/**
 * Check for layout shift during page load
 */
export async function measureLayoutShift(
  page: Page,
  url: string
): Promise<{ cls: number; issues: string[] }> {
  const issues: string[] = [];
  
  // Navigate and measure CLS
  await page.goto(url, { waitUntil: 'networkidle' });
  
  const cls = await page.evaluate(() => {
    return new Promise<number>((resolve) => {
      let clsValue = 0;
      
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'layout-shift' && !(entry as LayoutShift).hadRecentInput) {
            clsValue += (entry as LayoutShift).value;
          }
        }
      });
      
      observer.observe({ type: 'layout-shift', buffered: true });
      
      // Wait a bit for any layout shifts
      setTimeout(() => {
        observer.disconnect();
        resolve(clsValue);
      }, 2000);
    });
  });

  // CLS threshold: 0.1 is good, 0.25 needs improvement
  if (cls > 0.1) {
    issues.push(`Cumulative Layout Shift (CLS) is ${cls.toFixed(3)}, should be < 0.1`);
  }

  return { cls, issues };
}

/**
 * Validate table responsiveness
 */
export async function validateTableResponsiveness(
  page: Page,
  tableSelector: string
): Promise<CSSValidationResult> {
  const issues: string[] = [];
  
  const tableInfo = await page.evaluate((selector) => {
    const table = document.querySelector(selector);
    if (!table) return null;
    
    const rect = table.getBoundingClientRect();
    const parent = table.parentElement;
    const parentRect = parent?.getBoundingClientRect();
    
    return {
      tableWidth: rect.width,
      parentWidth: parentRect?.width ?? 0,
      hasHorizontalScroll: parent ? parent.scrollWidth > parent.clientWidth : false,
    };
  }, tableSelector);

  if (!tableInfo) {
    issues.push(`Table not found: ${tableSelector}`);
    return { valid: false, issues };
  }

  // Check if table overflows parent
  if (tableInfo.tableWidth > tableInfo.parentWidth && !tableInfo.hasHorizontalScroll) {
    issues.push(
      `Table width (${tableInfo.tableWidth}px) exceeds parent (${tableInfo.parentWidth}px) without scroll`
    );
  }

  return {
    valid: issues.length === 0,
    issues,
    metrics: {
      width: tableInfo.tableWidth,
      height: tableInfo.parentWidth,
      x: 0,
      y: 0,
    },
  };
}

/**
 * Test responsive layout at all breakpoints
 */
export async function testResponsiveLayout(
  page: Page,
  testFn: (breakpoint: ResponsiveBreakpoint) => Promise<void>
): Promise<void> {
  for (const breakpoint of BREAKPOINTS) {
    await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
    await testFn(breakpoint);
  }
}