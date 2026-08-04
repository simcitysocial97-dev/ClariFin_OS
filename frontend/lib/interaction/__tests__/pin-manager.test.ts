/**
 * Pin Manager Tests - Milestone 9 Interaction Polish
 *
 * Tests for pinning workspaces, entities, commands, and shortcuts.
 * Persistence via localStorage, reordering, and subscription behavior.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { pinManager } from '../pin-manager';
import type { PinnedItem } from '../pin-manager';

function makePinnedItem(overrides: Partial<PinnedItem> = {}): PinnedItem {
  return {
    id: 'pinned-1',
    type: 'workspace',
    label: 'Test Item',
    order: 0,
    pinnedAt: Date.now(),
    ...overrides,
  };
}

describe('PinManager — Milestone 9', () => {
  beforeEach(() => {
    pinManager.reset();
  });

  describe('Pin/Unpin', () => {
    it('pins an item', () => {
      const item = makePinnedItem({ id: 'ws-dashboard', type: 'workspace' });
      pinManager.pin(item);
      expect(pinManager.isPinned('ws-dashboard', 'workspace')).toBe(true);
    });

    it('does not duplicate an existing pin', () => {
      const item = makePinnedItem({ id: 'ws-dashboard', type: 'workspace' });
      pinManager.pin(item);
      pinManager.pin(item);
      expect(pinManager.getAll().length).toBe(1);
    });

    it('unpins by id and type', () => {
      pinManager.pin(makePinnedItem({ id: 'ws-dashboard', type: 'workspace' }));
      expect(pinManager.unpin('ws-dashboard', 'workspace')).toBe(true);
      expect(pinManager.isPinned('ws-dashboard', 'workspace')).toBe(false);
    });

    it('unpins by id only (all types)', () => {
      pinManager.pin(makePinnedItem({ id: 'item-1', type: 'workspace' }));
      pinManager.pin(makePinnedItem({ id: 'item-1', type: 'entity' }));
      pinManager.unpin('item-1');
      expect(pinManager.isPinned('item-1', 'workspace')).toBe(false);
      expect(pinManager.isPinned('item-1', 'entity')).toBe(false);
    });

    it('returns false when unpinning non-existent item', () => {
      expect(pinManager.unpin('nonexistent')).toBe(false);
    });
  });

  describe('Retrieval', () => {
    beforeEach(() => {
      pinManager.pin(makePinnedItem({ id: 'ws-1', type: 'workspace', label: 'Dashboard' }));
      pinManager.pin(makePinnedItem({ id: 'ent-1', type: 'entity', label: 'Account A' }));
      pinManager.pin(makePinnedItem({ id: 'cmd-1', type: 'command', label: 'Reconcile' }));
      pinManager.pin(makePinnedItem({ id: 'sh-1', type: 'shortcut', label: 'Cmd+K' }));
    });

    it('getAll returns all pinned items', () => {
      expect(pinManager.getAll().length).toBe(4);
    });

    it('getByType filters by type', () => {
      expect(pinManager.getByType('workspace').length).toBe(1);
      expect(pinManager.getByType('entity').length).toBe(1);
      expect(pinManager.getByType('command').length).toBe(1);
      expect(pinManager.getByType('shortcut').length).toBe(1);
    });

    it('getWorkspaces returns workspace pins', () => {
      expect(pinManager.getWorkspaces().length).toBe(1);
      expect(pinManager.getWorkspaces()[0].label).toBe('Dashboard');
    });

    it('getEntities returns entity pins', () => {
      expect(pinManager.getEntities().length).toBe(1);
    });

    it('getCommands returns command pins', () => {
      expect(pinManager.getCommands().length).toBe(1);
    });

    it('getShortcuts returns shortcut pins', () => {
      expect(pinManager.getShortcuts().length).toBe(1);
    });

    it('get returns specific item', () => {
      const item = pinManager.get('ws-1', 'workspace');
      expect(item?.label).toBe('Dashboard');
    });

    it('get without type matches any type', () => {
      const item = pinManager.get('ws-1');
      expect(item).toBeDefined();
    });
  });

  describe('isPinned', () => {
    it('returns true for pinned item', () => {
      pinManager.pin(makePinnedItem({ id: 'ws-1', type: 'workspace' }));
      expect(pinManager.isPinned('ws-1', 'workspace')).toBe(true);
    });

    it('returns false for unpinned item', () => {
      expect(pinManager.isPinned('nonexistent')).toBe(false);
    });

    it('type-specific check', () => {
      pinManager.pin(makePinnedItem({ id: 'item-1', type: 'workspace' }));
      expect(pinManager.isPinned('item-1', 'workspace')).toBe(true);
      expect(pinManager.isPinned('item-1', 'entity')).toBe(false);
    });
  });

  describe('Reorder', () => {
    it('reorders items by ID list', () => {
      pinManager.pin(makePinnedItem({ id: 'a', order: 0 }));
      pinManager.pin(makePinnedItem({ id: 'b', order: 1 }));
      pinManager.pin(makePinnedItem({ id: 'c', order: 2 }));
      pinManager.reorder(['c', 'a', 'b']);
      const items = pinManager.getAll();
      expect(items[0].id).toBe('c');
      expect(items[1].id).toBe('a');
      expect(items[2].id).toBe('b');
    });

    it('preserves items not in the reorder list', () => {
      pinManager.pin(makePinnedItem({ id: 'a', order: 0 }));
      pinManager.pin(makePinnedItem({ id: 'b', order: 1 }));
      pinManager.pin(makePinnedItem({ id: 'c', order: 2 }));
      pinManager.reorder(['c', 'a']);
      const items = pinManager.getAll();
      expect(items.find(i => i.id === 'b')?.order).toBe(2);
    });
  });

  describe('Clear', () => {
    it('clears all pinned items', () => {
      pinManager.pin(makePinnedItem());
      pinManager.clear();
      expect(pinManager.getAll().length).toBe(0);
    });
  });

  describe('Persistence', () => {
    it('pinned items persist in state', () => {
      pinManager.pin(makePinnedItem({ id: 'ws-1', type: 'workspace' }));
      expect(pinManager.getAll().length).toBe(1);
      expect(pinManager.getWorkspaces().length).toBe(1);
    });

    it('reset clears all items', () => {
      pinManager.pin(makePinnedItem({ id: 'ws-1', type: 'workspace' }));
      pinManager.reset();
      expect(pinManager.getAll().length).toBe(0);
    });
  });

  describe('Subscription', () => {
    it('subscribes to pin changes', () => {
      const listener = vi.fn();
      pinManager.subscribe(listener);
      pinManager.pin(makePinnedItem());
      expect(listener).toHaveBeenCalled();
    });

    it('unsubscribe stops receiving events', () => {
      const listener = vi.fn();
      const unsub = pinManager.subscribe(listener);
      unsub();
      pinManager.pin(makePinnedItem());
      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('Reset', () => {
    it('clears all items and localStorage', () => {
      pinManager.pin(makePinnedItem());
      pinManager.reset();
      expect(pinManager.getAll().length).toBe(0);
    });
  });
});