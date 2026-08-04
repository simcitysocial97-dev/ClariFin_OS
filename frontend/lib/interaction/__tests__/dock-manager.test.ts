/**
 * Dock Manager Tests - Milestone 9 Interaction Polish
 *
 * Tests for dock/undock panel management, visibility,
 * pinning, layout persistence, and subscription behavior.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { dockManager } from '../dock-manager';
import type { DockItem, DockLayout } from '../dock-manager';

function makeDockItem(overrides: Partial<DockItem> = {}): DockItem {
  return {
    id: 'test-panel',
    label: 'Test Panel',
    position: 'right',
    state: 'docked',
    size: { width: 300, height: 400 },
    zIndex: 1,
    pinned: false,
    visible: true,
    ...overrides,
  };
}

describe('DockManager — Milestone 9', () => {
  beforeEach(() => {
    dockManager.reset();
  });

  describe('Registration', () => {
    it('registers a dock item', () => {
      const item = dockManager.register(makeDockItem());
      expect(item.id).toBe('test-panel');
      expect(dockManager.getAll().length).toBe(1);
    });

    it('does not duplicate an existing item', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      expect(dockManager.getAll().length).toBe(1);
    });

    it('unregisters an item', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      expect(dockManager.unregister('panel-1')).toBe(true);
      expect(dockManager.getAll().length).toBe(0);
    });

    it('returns false when unregistering non-existent item', () => {
      expect(dockManager.unregister('nonexistent')).toBe(false);
    });

    it('gets an item by ID', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      expect(dockManager.get('panel-1')?.label).toBe('Test Panel');
    });

    it('returns undefined for missing item', () => {
      expect(dockManager.get('nonexistent')).toBeUndefined();
    });
  });

  describe('Dock/Float/Collapse/Hide', () => {
    beforeEach(() => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
    });

    it('docks an item to a position', () => {
      dockManager.dock('panel-1', 'left');
      const item = dockManager.get('panel-1');
      expect(item?.state).toBe('docked');
      expect(item?.position).toBe('left');
      expect(item?.visible).toBe(true);
    });

    it('floats an item', () => {
      dockManager.float('panel-1');
      const item = dockManager.get('panel-1');
      expect(item?.state).toBe('floating');
      expect(item?.visible).toBe(true);
    });

    it('collapses an item', () => {
      dockManager.collapse('panel-1');
      const item = dockManager.get('panel-1');
      expect(item?.state).toBe('collapsed');
      expect(item?.visible).toBe(false);
    });

    it('hides an item', () => {
      dockManager.hide('panel-1');
      const item = dockManager.get('panel-1');
      expect(item?.state).toBe('hidden');
      expect(item?.visible).toBe(false);
    });

    it('shows a hidden item', () => {
      dockManager.hide('panel-1');
      dockManager.show('panel-1');
      const item = dockManager.get('panel-1');
      expect(item?.visible).toBe(true);
      expect(item?.state).toBe('docked');
    });
  });

  describe('Active Item', () => {
    it('sets active item', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      dockManager.setActive('panel-1');
      expect(dockManager.getActive()?.id).toBe('panel-1');
    });

    it('sets active to null', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      dockManager.setActive('panel-1');
      dockManager.setActive(null);
      expect(dockManager.getActive()).toBeUndefined();
    });

    it('clears active when active item is collapsed', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      dockManager.setActive('panel-1');
      dockManager.collapse('panel-1');
      expect(dockManager.getActive()).toBeUndefined();
    });
  });

  describe('Filtering', () => {
    beforeEach(() => {
      dockManager.register(makeDockItem({ id: 'docked-panel', position: 'right', state: 'docked', visible: true }));
      dockManager.register(makeDockItem({ id: 'floating-panel', state: 'floating', visible: true }));
      dockManager.register(makeDockItem({ id: 'hidden-panel', state: 'hidden', visible: false }));
      dockManager.register(makeDockItem({ id: 'collapsed-panel', state: 'collapsed', visible: false }));
    });

    it('getDocked returns only docked visible items', () => {
      const docked = dockManager.getDocked();
      expect(docked.length).toBe(1);
      expect(docked[0].id).toBe('docked-panel');
    });

    it('getFloating returns only floating items', () => {
      const floating = dockManager.getFloating();
      expect(floating.length).toBe(1);
      expect(floating[0].id).toBe('floating-panel');
    });

    it('getVisible returns only visible items', () => {
      const visible = dockManager.getVisible();
      expect(visible.length).toBe(2);
    });
  });

  describe('Size and Position', () => {
    it('sets item size', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      dockManager.setSize('panel-1', { width: 500, height: 600 });
      const item = dockManager.get('panel-1');
      expect(item?.size).toEqual({ width: 500, height: 600 });
    });

    it('sets item position', () => {
      dockManager.register(makeDockItem({ id: 'panel-1', position: 'right' }));
      dockManager.setPosition('panel-1', 'bottom');
      const item = dockManager.get('panel-1');
      expect(item?.position).toBe('bottom');
    });
  });

  describe('Pin/Unpin', () => {
    it('pins an item', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      dockManager.pin('panel-1');
      expect(dockManager.isPinned('panel-1')).toBe(true);
    });

    it('unpins an item', () => {
      dockManager.register(makeDockItem({ id: 'panel-1', pinned: true }));
      dockManager.unpin('panel-1');
      expect(dockManager.isPinned('panel-1')).toBe(false);
    });

    it('isPinned returns false for non-existent item', () => {
      expect(dockManager.isPinned('nonexistent')).toBe(false);
    });
  });

  describe('Layout Persistence', () => {
    it('saveLayout returns current layout', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      const layout = dockManager.saveLayout();
      expect(layout.items.length).toBe(1);
      expect(layout.activeId).toBeNull();
    });

    it('restoreLayout replaces current layout', () => {
      dockManager.register(makeDockItem({ id: 'panel-1' }));
      const newLayout: DockLayout = {
        items: [makeDockItem({ id: 'panel-2' })],
        activeId: 'panel-2',
      };
      dockManager.restoreLayout(newLayout);
      expect(dockManager.getAll().length).toBe(1);
      expect(dockManager.get('panel-2')?.id).toBe('panel-2');
    });
  });

  describe('Reorder', () => {
    it('reorders items by ID list', () => {
      dockManager.register(makeDockItem({ id: 'a' }));
      dockManager.register(makeDockItem({ id: 'b' }));
      dockManager.register(makeDockItem({ id: 'c' }));
      dockManager.reorder(['c', 'a', 'b']);
      const items = dockManager.getAll();
      expect(items[0].id).toBe('c');
      expect(items[1].id).toBe('a');
      expect(items[2].id).toBe('b');
    });
  });

  describe('Subscription', () => {
    it('subscribes to layout changes', () => {
      const listener = vi.fn();
      dockManager.subscribe(listener);
      dockManager.register(makeDockItem());
      expect(listener).toHaveBeenCalled();
    });

    it('unsubscribe stops receiving events', () => {
      const listener = vi.fn();
      const unsub = dockManager.subscribe(listener);
      unsub();
      dockManager.register(makeDockItem());
      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('Reset', () => {
    it('clears all items', () => {
      dockManager.register(makeDockItem());
      dockManager.reset();
      expect(dockManager.getAll().length).toBe(0);
    });
  });
});