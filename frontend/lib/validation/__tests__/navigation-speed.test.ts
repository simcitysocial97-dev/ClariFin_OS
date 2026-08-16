/**
 * Navigation Speed Validation - Milestone 10 Experience Validation
 *
 * End-to-end validation of navigation speed across workspace switches,
 * breadcrumb updates, and deep link resolution.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { navigationRuntime, resetNavigationRuntime } from '../../runtime/navigation-runtime';
import { workspaceRuntime, resetWorkspaceRuntime } from '../../runtime/workspace-runtime';
import { undoManager } from '../../interaction/undo-manager';

describe('Navigation Speed Validation — Milestone 10', () => {
  beforeEach(() => {
    resetNavigationRuntime();
    resetWorkspaceRuntime();
    undoManager.clear();
  });

  describe('Workspace Switch Speed', () => {
    it('workspace switch completes under 100ms for cached workspace', () => {
      workspaceRuntime.navigateTo('dashboard');
      workspaceRuntime.navigateTo('transactions');

      const start = performance.now();
      workspaceRuntime.navigateTo('dashboard');
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(100);
    });

    it('workspace switch completes under 200ms for cold mount', () => {
      const start = performance.now();
      workspaceRuntime.navigateTo('dashboard');
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(200);
    });
  });

  describe('Breadcrumb Update Speed', () => {
    it('breadcrumb update completes under 10ms', () => {
      const start = performance.now();
      workspaceRuntime.setBreadcrumbs(['Dashboard', 'Transactions', 'Details']);
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(10);
    });

    it('breadcrumb trail has correct depth', () => {
      workspaceRuntime.setBreadcrumbs(['Dashboard', 'Transactions', 'Details']);
      const state = workspaceRuntime.state;
      expect(state.breadcrumbs.length).toBe(3);
      expect(state.breadcrumbs[0]).toBe('Dashboard');
      expect(state.breadcrumbs[2]).toBe('Details');
    });
  });

  describe('Deep Link Resolution Speed', () => {
    it('deep link navigation completes under 50ms', () => {
      const start = performance.now();
      navigationRuntime.pushPath('/transactions?category=food', 'transactions');
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(50);
    });

    it('deep link preserves query parameters', () => {
      navigationRuntime.pushPath('/transactions?category=food&date=2024-01-15', 'transactions');
      const current = navigationRuntime.current;
      expect(current?.path).toContain('category=food');
      expect(current?.path).toContain('date=2024-01-15');
    });
  });

  describe('Navigation History', () => {
    it('navigation history tracks entries correctly', () => {
      navigationRuntime.pushPath('/dashboard');
      navigationRuntime.pushPath('/transactions');
      navigationRuntime.pushPath('/accounts');

      expect(navigationRuntime.canGoBack).toBe(true);
      expect(navigationRuntime.state.history.length).toBe(3);
    });

    it('back navigation restores previous workspace', () => {
      navigationRuntime.pushPath('/dashboard');
      navigationRuntime.pushPath('/transactions');
      navigationRuntime.goBack();
      const current = navigationRuntime.current;
      expect(current?.path).toBe('/dashboard');
    });

    it('forward navigation restores next workspace', () => {
      navigationRuntime.pushPath('/dashboard');
      navigationRuntime.pushPath('/transactions');
      navigationRuntime.goBack();
      navigationRuntime.goForward();
      const current = navigationRuntime.current;
      expect(current?.path).toBe('/transactions');
    });
  });

  describe('Undo/Redo for Navigation', () => {
    it('undo manager tracks navigation actions', async () => {
      const undoFn = vi.fn();
      const redoFn = vi.fn();
      undoManager.registerAction({
        type: 'navigation',
        label: 'Navigate to Dashboard',
        undo: undoFn,
        redo: redoFn,
      });
      expect(undoManager.canUndo()).toBe(true);
      await undoManager.undo();
      expect(undoFn).toHaveBeenCalledOnce();
      expect(undoManager.canRedo()).toBe(true);
      await undoManager.redo();
      expect(redoFn).toHaveBeenCalledOnce();
    });
  });
});
