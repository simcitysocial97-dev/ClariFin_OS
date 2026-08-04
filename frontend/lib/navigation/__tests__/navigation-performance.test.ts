/**
 * Navigation Performance Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Performance tests for navigation utilities.
 */

import { describe, it, expect } from 'vitest';
import { parseNavigationState, buildNavigationUrl } from '../persistence';
import { isNavigationShortcut } from '../keyboard';

describe('Navigation Performance', () => {
  it('parses navigation state under 50ms', () => {
    const start = performance.now();
    for (let i = 0; i < 1000; i++) {
      parseNavigationState('/transactions?category=food&date=2024-01-15&merchant=test');
    }
    const end = performance.now();
    const avg = (end - start) / 1000;
    expect(avg).toBeLessThan(0.05);
  });

  it('builds navigation URL under 50ms', () => {
    const start = performance.now();
    for (let i = 0; i < 1000; i++) {
      buildNavigationUrl('/transactions', { category: 'food', date: '2024-01-15' });
    }
    const end = performance.now();
    const avg = (end - start) / 1000;
    expect(avg).toBeLessThan(0.05);
  });

  it('checks navigation shortcut under 50ms', () => {
    const event = { altKey: true, key: 'ArrowLeft' } as unknown as KeyboardEvent;
    const start = performance.now();
    for (let i = 0; i < 1000; i++) {
      isNavigationShortcut(event);
    }
    const end = performance.now();
    const avg = (end - start) / 1000;
    expect(avg).toBeLessThan(0.05);
  });
});