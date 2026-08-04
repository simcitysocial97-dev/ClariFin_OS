/**
 * Undo Manager Tests - Milestone 9 Interaction Polish
 *
 * Tests for undo/redo stack management, action grouping,
 * snapshot/restore, and subscription behavior.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UndoManager } from '../undo-manager';
import type { UndoAction } from '../undo-manager';

function makeAction(
  overrides: Partial<Omit<UndoAction, 'id' | 'timestamp'>> = {},
): Omit<UndoAction, 'id' | 'timestamp'> {
  return {
    type: 'test',
    label: 'Test Action',
    undo: vi.fn(),
    redo: vi.fn(),
    ...overrides,
  };
}

describe('UndoManager — Milestone 9', () => {
  let manager: UndoManager;

  beforeEach(() => {
    manager = new UndoManager();
  });

  describe('Action Registration', () => {
    it('registers an action and returns its ID', () => {
      const id = manager.registerAction(makeAction());
      expect(id).toMatch(/^undo-/);
      expect(manager.getPastActions().length).toBe(1);
    });

    it('clears future when a new action is registered', async () => {
      manager.registerAction(makeAction({ label: 'first' }));
      manager.registerAction(makeAction({ label: 'second' }));
      expect(manager.canUndo()).toBe(true);
      // Undo to create future
      await manager.undo();
      expect(manager.canRedo()).toBe(true);
      // New action should clear future
      manager.registerAction(makeAction({ label: 'third' }));
      expect(manager.canRedo()).toBe(false);
    });

    it('enforces max history limit', () => {
      const smallManager = new UndoManager(3);
      for (let i = 0; i < 5; i++) {
        smallManager.registerAction(makeAction({ label: `action-${i}` }));
      }
      expect(smallManager.getPastActions().length).toBe(3);
    });

    it('assigns unique IDs', () => {
      const id1 = manager.registerAction(makeAction());
      const id2 = manager.registerAction(makeAction());
      expect(id1).not.toBe(id2);
    });

    it('assigns timestamp on registration', () => {
      const before = Date.now();
      const action = makeAction();
      const id = manager.registerAction(action);
      const after = Date.now();
      const past = manager.getPastActions().find(a => a.id === id);
      expect(past?.timestamp).toBeGreaterThanOrEqual(before);
      expect(past?.timestamp).toBeLessThanOrEqual(after);
    });
  });

  describe('Undo', () => {
    it('executes undo and moves action to future', async () => {
      const undoFn = vi.fn();
      manager.registerAction(makeAction({ undo: undoFn }));
      expect(manager.canUndo()).toBe(true);
      expect(manager.canRedo()).toBe(false);

      const result = await manager.undo();
      expect(result).toBe(true);
      expect(undoFn).toHaveBeenCalledOnce();
      expect(manager.canUndo()).toBe(false);
      expect(manager.canRedo()).toBe(true);
    });

    it('returns false when nothing to undo', async () => {
      const result = await manager.undo();
      expect(result).toBe(false);
    });

    it('handles undo with multiple actions in LIFO order', async () => {
      const undo1 = vi.fn();
      const undo2 = vi.fn();
      manager.registerAction(makeAction({ label: 'first', undo: undo1 }));
      manager.registerAction(makeAction({ label: 'second', undo: undo2 }));

      await manager.undo();
      expect(undo2).toHaveBeenCalledOnce();
      expect(undo1).not.toHaveBeenCalled();
    });

    it('restores action on undo failure', async () => {
      const undoFn = vi.fn().mockRejectedValue(new Error('undo failed'));
      manager.registerAction(makeAction({ undo: undoFn }));
      const result = await manager.undo();
      expect(result).toBe(false);
      expect(manager.canUndo()).toBe(true);
    });
  });

  describe('Redo', () => {
    it('executes redo and moves action back to past', async () => {
      const redoFn = vi.fn();
      manager.registerAction(makeAction({ redo: redoFn }));
      await manager.undo();
      const result = await manager.redo();
      expect(result).toBe(true);
      expect(redoFn).toHaveBeenCalledOnce();
      expect(manager.canUndo()).toBe(true);
      expect(manager.canRedo()).toBe(false);
    });

    it('returns false when nothing to redo', async () => {
      const result = await manager.redo();
      expect(result).toBe(false);
    });

    it('restores action on redo failure', async () => {
      const redoFn = vi.fn().mockRejectedValue(new Error('redo failed'));
      manager.registerAction(makeAction({ redo: redoFn }));
      await manager.undo();
      const result = await manager.redo();
      expect(result).toBe(false);
      expect(manager.canRedo()).toBe(true);
    });
  });

  describe('State Management', () => {
    it('reports idle state by default', () => {
      expect(manager.getState()).toBe('idle');
    });

    it('reports undoing state during undo', async () => {
      manager.registerAction(makeAction());
      const promise = manager.undo();
      expect(manager.getState()).toBe('undoing');
      await promise;
      expect(manager.getState()).toBe('idle');
    });

    it('reports redoing state during redo', async () => {
      manager.registerAction(makeAction());
      await manager.undo();
      const promise = manager.redo();
      expect(manager.getState()).toBe('redoing');
      await promise;
      expect(manager.getState()).toBe('idle');
    });
  });

  describe('History Access', () => {
    it('getHistory returns all actions', () => {
      manager.registerAction(makeAction({ label: 'a' }));
      manager.registerAction(makeAction({ label: 'b' }));
      expect(manager.getHistory().length).toBe(2);
    });

    it('getPastActions returns past actions only', () => {
      manager.registerAction(makeAction({ label: 'a' }));
      manager.registerAction(makeAction({ label: 'b' }));
      expect(manager.getPastActions().length).toBe(2);
    });

    it('getFutureActions returns future actions after undo', async () => {
      manager.registerAction(makeAction());
      await manager.undo();
      expect(manager.getFutureActions().length).toBe(1);
      expect(manager.getPastActions().length).toBe(0);
    });

    it('canUndo returns true when actions exist', () => {
      manager.registerAction(makeAction());
      expect(manager.canUndo()).toBe(true);
    });

    it('canRedo returns false when no future actions', () => {
      manager.registerAction(makeAction());
      expect(manager.canRedo()).toBe(false);
    });
  });

  describe('Clear', () => {
    it('clears all history', () => {
      manager.registerAction(makeAction());
      manager.clear();
      expect(manager.canUndo()).toBe(false);
      expect(manager.canRedo()).toBe(false);
      expect(manager.getHistory().length).toBe(0);
    });
  });

  describe('Snapshot and Restore', () => {
    it('snapshot captures current state', () => {
      manager.registerAction(makeAction({ label: 'a' }));
      const snap = manager.snapshot();
      expect(snap.past.length).toBe(1);
      expect(snap.future.length).toBe(0);
    });

    it('restore reverts to snapshot state', async () => {
      manager.registerAction(makeAction({ label: 'a' }));
      manager.registerAction(makeAction({ label: 'b' }));
      const snap = manager.snapshot();

      manager.registerAction(makeAction({ label: 'c' }));
      expect(manager.getPastActions().length).toBe(3);

      manager.restore(snap);
      expect(manager.getPastActions().length).toBe(2);
    });
  });

  describe('Action Grouping', () => {
    it('groups multiple actions with a label', () => {
      const ids = manager.groupActions('group-1', [
        makeAction({ type: 'a', label: 'Action A' }),
        makeAction({ type: 'b', label: 'Action B' }),
        makeAction({ type: 'c', label: 'Action C' }),
      ]);
      expect(ids.length).toBe(3);
      expect(manager.getPastActions().length).toBe(3);
    });

    it('retrieves group label for an action', () => {
      const ids = manager.groupActions('Bulk Edit', [
        makeAction({ type: 'x', label: 'Edit A' }),
      ]);
      expect(manager.getActionLabel(ids[0])).toBe('Bulk Edit');
    });
  });

  describe('Labels', () => {
    it('getUndoLabel returns the label of the last action', () => {
      manager.registerAction(makeAction({ label: 'Delete Transaction' }));
      expect(manager.getUndoLabel()).toBe('Delete Transaction');
    });

    it('getRedoLabel returns the label of the next future action', async () => {
      manager.registerAction(makeAction({ label: 'Create Account' }));
      await manager.undo();
      expect(manager.getRedoLabel()).toBe('Create Account');
    });

    it('getUndoLabel returns null when no history', () => {
      expect(manager.getUndoLabel()).toBeNull();
    });

    it('getRedoLabel returns null when no future', () => {
      expect(manager.getRedoLabel()).toBeNull();
    });
  });

  describe('Subscription', () => {
    it('subscribes to state changes', () => {
      const listener = vi.fn();
      manager.subscribe(listener);
      manager.registerAction(makeAction());
      expect(listener).toHaveBeenCalled();
    });

    it('unsubscribe stops receiving notifications', () => {
      const listener = vi.fn();
      const unsub = manager.subscribe(listener);
      unsub();
      manager.registerAction(makeAction());
      expect(listener).not.toHaveBeenCalled();
    });

    it('notifies on undo and redo', async () => {
      const listener = vi.fn();
      manager.subscribe(listener);
      manager.registerAction(makeAction());
      listener.mockClear();
      await manager.undo();
      expect(listener).toHaveBeenCalled();
      listener.mockClear();
      await manager.redo();
      expect(listener).toHaveBeenCalled();
    });
  });

  describe('createStateAction', () => {
    it('creates action with undo applying before state', () => {
      const applied: number[] = [];
      const stateAction = UndoManager.createStateAction({
        type: 'set',
        label: 'Set Value',
        before: 10,
        after: 20,
        apply: (v: number) => applied.push(v),
      });
      stateAction.undo();
      expect(applied).toEqual([10]);
    });

    it('creates action with redo applying after state', () => {
      const applied: number[] = [];
      const stateAction = UndoManager.createStateAction({
        type: 'set',
        label: 'Set Value',
        before: 10,
        after: 20,
        apply: (v: number) => applied.push(v),
      });
      stateAction.redo();
      expect(applied).toEqual([20]);
    });
  });

  describe('setMaxHistory', () => {
    it('truncates past history when max is reduced', () => {
      manager.registerAction(makeAction({ label: 'a' }));
      manager.registerAction(makeAction({ label: 'b' }));
      manager.registerAction(makeAction({ label: 'c' }));
      manager.setMaxHistory(2);
      expect(manager.getPastActions().length).toBe(2);
    });

    it('truncates future history when max is reduced', async () => {
      manager.registerAction(makeAction({ label: 'a' }));
      manager.registerAction(makeAction({ label: 'b' }));
      await manager.undo();
      await manager.undo();
      manager.setMaxHistory(1);
      expect(manager.getFutureActions().length).toBe(1);
    });
  });
});
