/**
 * Drag Manager - Milestone 9 Interaction Polish
 *
 * Manages drag-and-drop state across the OS shell.
 * Centralized state for drag operations, drop targets, and drag feedback.
 *
 * Drag/Drop rules per architecture §8.12 and §8.13:
 * - Selection state (dragging entities) is managed by SelectionRuntime, not this manager.
 * - This manager tracks the ephemeral drag session only.
 */

export type DragData = Record<string, unknown> & { type: string };

export interface DragState {
  isDragging: boolean;
  activeId: string | null;
  activeType: string | null;
  data: DragData | null;
  position: { x: number; y: number } | null;
  sourceWorkspace: string | null;
}

export interface DropTarget {
  id: string;
  type: string;
  accepts: string[];
  element: HTMLElement | null;
}

export interface DragSession {
  id: string;
  state: DragState;
  startTime: number;
  dropTargets: Map<string, DropTarget>;
  hoveredTarget: string | null;
  listeners: Set<(state: DragState) => void>;
}

class DragManager {
  private session: DragSession | null = null;
  private sessions: Map<string, DragSession> = new Map();

  startDrag(data: DragData, sourceWorkspace: string | null = null): string {
    const sessionId = `drag-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const session: DragSession = {
      id: sessionId,
      state: {
        isDragging: true,
        activeId: typeof data.id === 'string' ? data.id : null,
        activeType: data.type,
        data,
        position: null,
        sourceWorkspace,
      },
      startTime: Date.now(),
      dropTargets: new Map(),
      hoveredTarget: null,
      listeners: new Set(),
    };

    this.session = session;
    this.sessions.set(sessionId, session);
    this.notify(session);
    return sessionId;
  }

  updatePosition(sessionId: string, x: number, y: number): void {
    const session = this.sessions.get(sessionId);
    if (!session) return;
    session.state.position = { x, y };
    this.notify(session);
  }

  registerDropTarget(target: DropTarget): void {
    if (!this.session) return;
    this.session.dropTargets.set(target.id, target);
  }

  unregisterDropTarget(targetId: string): boolean {
    const session = this.session;
    if (!session) return false;
    return session.dropTargets.delete(targetId);
  }

  getDropTargets(): DropTarget[] {
    return Array.from(this.session?.dropTargets.values() ?? []);
  }

  getDropTarget(id: string): DropTarget | undefined {
    return this.session?.dropTargets.get(id);
  }

  getAcceptableTargets(dragDataType: string): DropTarget[] {
    return this.getDropTargets().filter(t =>
      t.accepts.some(type => type === dragDataType || type === '*'),
    );
  }

  hoverTarget(targetId: string): void {
    const session = this.session;
    if (!session) return;
    session.hoveredTarget = targetId;
    this.notify(session);
  }

  drop(_targetId: string | null): DragData | null {
    const session = this.session;
    if (!session) return null;

    const result = session.state.data;
    session.state.isDragging = false;
    session.state.position = null;
    session.hoveredTarget = null;
    this.notify(session);

    return result;
  }

  cancelDrag(): void {
    if (!this.session) return;
    const session = this.session;
    session.state.isDragging = false;
    session.state.position = null;
    session.hoveredTarget = null;
    this.notify(session);
    this.sessions.delete(session.id);
    this.session = null;
  }

  endDrag(targetId: string | null): { data: DragData | null; targetId: string | null } {
    if (!this.session) return { data: null, targetId: null };

    const session = this.session;
    const data = session.state.data;
    if (targetId) {
      session.hoveredTarget = targetId;
    }

    session.state.isDragging = false;
    session.state.position = null;
    this.notify(session);

    this.sessions.delete(session.id);
    this.session = null;
    return { data, targetId };
  }

  getActiveSession(): DragSession | null {
    return this.session;
  }

  getState(): DragState {
    if (!this.session) {
      return {
        isDragging: false,
        activeId: null,
        activeType: null,
        data: null,
        position: null,
        sourceWorkspace: null,
      };
    }
    return { ...this.session.state, position: this.session.state.position };
  }

  subscribe(listener: (state: DragState) => void): () => void {
    if (!this.session) return () => {};
    this.session.listeners.add(listener);
    return () => {
      this.session?.listeners.delete(listener);
    };
  }

  private notify(session: DragSession): void {
    for (const listener of session.listeners) {
      try {
        listener({ ...session.state, position: session.state.position });
      } catch (err) {
        console.error('[DragManager] Listener error:', err);
      }
    }
  }

  reset(): void {
    for (const session of this.sessions.values()) {
      session.listeners.clear();
    }
    this.sessions.clear();
    this.session = null;
  }
}

const dragManager = new DragManager();

export { dragManager, DragManager };
