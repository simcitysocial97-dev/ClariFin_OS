/**
 * Keyboard Registry Tests - Milestone 9 Interaction Polish
 *
 * Tests for shortcut registration, usage tracking,
 * favorites, aliases, and workspace-scoped retrieval.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { keyboardRegistry } from '../keyboard-registry';
import type { KeyboardShortcut } from '../interaction-types';

function makeShortcut(
  key: string,
  overrides: Partial<KeyboardShortcut> = {},
): KeyboardShortcut {
  return {
    key,
    handler: vi.fn(),
    description: 'test shortcut',
    category: 'system',
    ...overrides,
  };
}

describe('KeyboardRegistry — Milestone 9', () => {
  beforeEach(() => {
    keyboardRegistry.reset();
  });

  describe('Registration', () => {
    it('registers a single shortcut', () => {
      const shortcut = makeShortcut('a', { description: 'workspace: test' });
      keyboardRegistry.register(shortcut);
      expect(keyboardRegistry.getAll().length).toBe(1);
    });

    it('registers multiple shortcuts', () => {
      keyboardRegistry.registerAll([
        makeShortcut('a'),
        makeShortcut('b'),
        makeShortcut('c'),
      ]);
      expect(keyboardRegistry.getAll().length).toBe(3);
    });

    it('unregisters a shortcut by key', () => {
      const shortcut = makeShortcut('a');
      keyboardRegistry.register(shortcut);
      expect(keyboardRegistry.unregister('a')).toBe(true);
      expect(keyboardRegistry.getAll().length).toBe(0);
    });

    it('returns false when unregistering non-existent key', () => {
      expect(keyboardRegistry.unregister('nonexistent')).toBe(false);
    });
  });

  describe('Retrieval', () => {
    it('gets a shortcut by key', () => {
      const shortcut = makeShortcut('k', { ctrl: true });
      keyboardRegistry.register(shortcut);
      expect(keyboardRegistry.get('ctrl+k')).toBeDefined();
      expect(keyboardRegistry.get('ctrl+k')?.key).toBe('k');
    });

    it('returns undefined for missing key', () => {
      expect(keyboardRegistry.get('nonexistent')).toBeUndefined();
    });

    it('gets shortcuts by category', () => {
      keyboardRegistry.registerAll([
        makeShortcut('a', { category: 'navigation' }),
        makeShortcut('b', { category: 'search' }),
        makeShortcut('c', { category: 'navigation' }),
      ]);
      const navShortcuts = keyboardRegistry.getByCategory('navigation');
      expect(navShortcuts.length).toBe(2);
    });

    it('gets shortcuts for a workspace', () => {
      keyboardRegistry.registerAll([
        makeShortcut('a', { description: 'Switch to workspace dashboard' }),
        makeShortcut('b', { description: 'Switch to workspace transactions' }),
        makeShortcut('c', { description: 'General action' }),
      ]);
      const workspaceShortcuts = keyboardRegistry.getByWorkspace('dashboard');
      expect(workspaceShortcuts.length).toBe(1);
    });
  });

  describe('Usage Tracking', () => {
    it('records usage of a shortcut', () => {
      const shortcut = makeShortcut('a');
      keyboardRegistry.register(shortcut);
      keyboardRegistry.recordUsage(shortcut);
      const recent = keyboardRegistry.getRecent(10);
      expect(recent.length).toBe(1);
    });

    it('increments use count on repeated usage', () => {
      const shortcut = makeShortcut('a');
      keyboardRegistry.register(shortcut);
      keyboardRegistry.recordUsage(shortcut);
      keyboardRegistry.recordUsage(shortcut);
      keyboardRegistry.recordUsage(shortcut);
      const recent = keyboardRegistry.getRecent(10);
      expect(recent[0]).toEqual(shortcut);
    });

    it('returns most used shortcuts sorted by count', () => {
      const s1 = makeShortcut('a');
      const s2 = makeShortcut('b');
      keyboardRegistry.registerAll([s1, s2]);
      keyboardRegistry.recordUsage(s2);
      keyboardRegistry.recordUsage(s2);
      keyboardRegistry.recordUsage(s2);
      keyboardRegistry.recordUsage(s1);

      const mostUsed = keyboardRegistry.getMostUsed(2);
      expect(mostUsed[0]).toEqual(s2);
      expect(mostUsed[1]).toEqual(s1);
    });

    it('returns recent shortcuts sorted by last used', () => {
      const s1 = makeShortcut('a');
      const s2 = makeShortcut('b');
      keyboardRegistry.registerAll([s1, s2]);

      keyboardRegistry.recordUsage(s1);
      keyboardRegistry.recordUsage(s2);

      const recent = keyboardRegistry.getRecent(2);
      expect(recent.length).toBe(2);
      expect(recent.map(s => s.key)).toContain('a');
      expect(recent.map(s => s.key)).toContain('b');
    });
  });

  describe('Favorites', () => {
    it('adds to favorites', () => {
      const shortcut = makeShortcut('a');
      keyboardRegistry.register(shortcut);
      keyboardRegistry.addToFavorites(shortcut);
      expect(keyboardRegistry.getFavorites().length).toBe(1);
    });

    it('removes from favorites', () => {
      const shortcut = makeShortcut('a');
      keyboardRegistry.register(shortcut);
      keyboardRegistry.addToFavorites(shortcut);
      keyboardRegistry.removeFromFavorites(shortcut);
      expect(keyboardRegistry.getFavorites().length).toBe(0);
    });

    it('getFavorites returns only favorited shortcuts', () => {
      const s1 = makeShortcut('a');
      const s2 = makeShortcut('b');
      keyboardRegistry.registerAll([s1, s2]);
      keyboardRegistry.addToFavorites(s2);
      expect(keyboardRegistry.getFavorites()).toEqual([s2]);
    });
  });

  describe('Aliases', () => {
    it('resolves an alias to a shortcut', () => {
      const shortcut = makeShortcut('k', { ctrl: true });
      keyboardRegistry.register(shortcut);
      keyboardRegistry.addAlias('cmd-palette', shortcut);
      expect(keyboardRegistry.resolveAlias('cmd-palette')).toBeDefined();
      expect(keyboardRegistry.resolveAlias('cmd-palette')?.key).toBe('k');
    });

    it('returns undefined for unknown alias', () => {
      expect(keyboardRegistry.resolveAlias('unknown')).toBeUndefined();
    });

    it('alias lookup is case-insensitive', () => {
      const shortcut = makeShortcut('a');
      keyboardRegistry.register(shortcut);
      keyboardRegistry.addAlias('MyAlias', shortcut);
      expect(keyboardRegistry.resolveAlias('myalias')).toBeDefined();
      expect(keyboardRegistry.resolveAlias('MYALIAS')).toBeDefined();
    });
  });

  describe('Reset', () => {
    it('clears all state', () => {
      keyboardRegistry.register(makeShortcut('a'));
      keyboardRegistry.reset();
      expect(keyboardRegistry.getAll().length).toBe(0);
    });
  });
});
