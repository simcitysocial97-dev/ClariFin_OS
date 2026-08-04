/**
 * Undo Manager - Milestone 9 Interaction Polish
 *
 * General-purpose undo/redo stack for commands and state mutations.
 * Integrates with the Command Runtime for command history and
 * the Navigation Runtime for navigation history.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md — Milestone 9
 */

export interface UndoAction {
  id: string;
  type: string;
  label: string;
  timestamp: number;
  undo: () => void | Promise<void>;
  redo: () => void | Promise<void>;
}

export type UndoManagerState = 'idle' | 'undoing' | 'redoing';

export interface UndoManagerSnapshot {
  past: UndoAction[];
  future: UndoAction[];
}

export interface StateSnapshotAction<T> {
  type: string;
  label: string;
  before: T;
  after: T;
  apply: (state: T) => void;
}

const DEFAULT_MAX_HISTORY = 200;

class UndoManager {
  private past: UndoAction[] = [];
  private future: UndoAction[] = [];
  private state: UndoManagerState = 'idle';
  private maxHistory: number;
  private listeners: Set<() => void> = new Set();
  private actionCounter = 0;
  private groups: Map<string, string> = new Map();

  constructor(maxHistory: number = DEFAULT_MAX_HISTORY) {
    this.maxHistory = maxHistory;
  }

  registerAction(action: Omit<UndoAction, 'id' | 'timestamp'>): string {
    const fullAction: UndoAction = {
      ...action,
      id: `undo-${Date.now()}-${this.actionCounter++}`,
      timestamp: Date.now(),
    };

    this.past.push(fullAction);
    this.future = [];

    if (this.past.length > this.maxHistory) {
      this.past.shift();
    }

    this.notify();
    return fullAction.id;
  }

  async undo(): Promise<boolean> {
    const action = this.past.pop();
    if (!action) return false;

    this.state = 'undoing';
    try {
      await action.undo();
      this.future.unshift(action);
      this.notify();
      return true;
    } catch (err) {
      this.past.push(action);
      this.notify();
      return false;
    } finally {
      this.state = 'idle';
    }
  }

  async redo(): Promise<boolean> {
    const action = this.future.shift();
    if (!action) return false;

    this.state = 'redoing';
    try {
      await action.redo();
      this.past.push(action);

      if (this.past.length > this.maxHistory) {
        this.past.shift();
      }

      this.notify();
      return true;
    } catch (err) {
      this.future.unshift(action);
      this.notify();
      return false;
    } finally {
      this.state = 'idle';
    }
  }

  canUndo(): boolean {
    return this.past.length > 0;
  }

  canRedo(): boolean {
    return this.future.length > 0;
  }

  getHistory(): UndoAction[] {
    return [...this.past, ...this.future];
  }

  getPastActions(): UndoAction[] {
    return [...this.past];
  }

  getFutureActions(): UndoAction[] {
    return [...this.future];
  }

  getState(): UndoManagerState {
    return this.state;
  }

  clear(): void {
    this.past = [];
    this.future = [];
    this.actionCounter = 0;
    this.groups.clear();
    this.notify();
  }

  snapshot(): UndoManagerSnapshot {
    return {
      past: [...this.past],
      future: [...this.future],
    };
  }

  restore(snapshot: UndoManagerSnapshot): void {
    this.past = [...snapshot.past];
    this.future = [...snapshot.future];
    this.notify();
  }

  setMaxHistory(max: number): void {
    this.maxHistory = max;
    while (this.past.length > this.maxHistory) {
      this.past.shift();
    }
    while (this.future.length > this.maxHistory) {
      this.future.pop();
    }
    this.notify();
  }

  groupActions(groupLabel: string, actions: Array<Omit<UndoAction, 'id' | 'timestamp'>>): string[] {
    const ids: string[] = [];
    for (const action of actions) {
      const id = this.registerAction(action);
      ids.push(id);
    }
    this.labelGroup(ids, groupLabel);
    return ids;
  }

  private labelGroup(actionIds: string[], label: string): void {
    for (const id of actionIds) {
      this.groups.set(id, label);
    }
  }

  getActionLabel(actionId: string): string | undefined {
    return this.groups.get(actionId);
  }

  getUndoLabel(): string | null {
    if (this.past.length === 0) return null;
    const lastAction = this.past[this.past.length - 1];
    return this.groups.get(lastAction.id) ?? lastAction.label;
  }

  getRedoLabel(): string | null {
    if (this.future.length === 0) return null;
    const nextAction = this.future[0];
    return this.groups.get(nextAction.id) ?? nextAction.label;
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      try {
        listener();
      } catch (err) {
        console.error('[UndoManager] Listener error:', err);
      }
    }
  }

  /**
   * Create an undo action from before/after state snapshots.
   * Undo applies the `before` state; Redo applies the `after` state.
   */
  static createStateAction<T>(
    def: StateSnapshotAction<T>,
  ): Omit<UndoAction, 'id' | 'timestamp'> {
    return {
      type: def.type,
      label: def.label,
      undo: () => def.apply(def.before),
      redo: () => def.apply(def.after),
    };
  }
}

const undoManager = new UndoManager();

export { undoManager, UndoManager };
