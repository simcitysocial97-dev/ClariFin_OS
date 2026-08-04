/**
 * Runtime Event Bus — Stage 9 Financial Operating System
 *
 * Inter-runtime publish/subscribe communication mechanism.
 * Fire-and-forget, synchronous delivery, error-isolated subscribers.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §9
 */

// ─── Base Event Interface ─────────────────────────────────────────────────────

export interface RuntimeEvent {
  type: string;
  timestamp: number;
  source: string;
  payload: Record<string, unknown>;
}

// ─── Selection Events ─────────────────────────────────────────────────────────

export const SELECTION_CHANGED = 'SelectionChanged';
export const SELECTION_CLEARED = 'SelectionCleared';
export const SELECTION_HIGHLIGHTED = 'SelectionHighlighted';

export interface SelectionChangedEvent extends RuntimeEvent {
  type: typeof SELECTION_CHANGED;
  payload: {
    activeEntityId: string | null;
    selectedIds: string[];
    selectionRange: { start: string; end: string } | null;
  };
}

export interface SelectionClearedEvent extends RuntimeEvent {
  type: typeof SELECTION_CLEARED;
  payload: { previousEntityId: string | null };
}

export interface SelectionHighlightedEvent extends RuntimeEvent {
  type: typeof SELECTION_HIGHLIGHTED;
  payload: { entityId: string; source: string };
}

// ─── Timeline Events ──────────────────────────────────────────────────────────

export const TIMELINE_CHANGED = 'TimelineChanged';
export const TIMELINE_GRANULARITY_CHANGED = 'TimelineGranularityChanged';
export const TIMELINE_SCRUBBED = 'TimelineScrubbed';

export interface TimelineChangedEvent extends RuntimeEvent {
  type: typeof TIMELINE_CHANGED;
  payload: {
    activePeriod: { start: string; end: string; label: string };
    granularity: 'day' | 'week' | 'month' | 'quarter' | 'year';
    comparisonPeriod: { start: string; end: string; label: string } | null;
  };
}

export interface TimelineGranularityChangedEvent extends RuntimeEvent {
  type: typeof TIMELINE_GRANULARITY_CHANGED;
  payload: { granularity: 'day' | 'week' | 'month' | 'quarter' | 'year' };
}

export interface TimelineScrubbedEvent extends RuntimeEvent {
  type: typeof TIMELINE_SCRUBBED;
  payload: { scrubPosition: number; period: { start: string; end: string } };
}

// ─── Workspace Events ─────────────────────────────────────────────────────────

export const WORKSPACE_OPENED = 'WorkspaceOpened';
export const WORKSPACE_CLOSED = 'WorkspaceClosed';
export const WORKSPACE_SWITCHED = 'WorkspaceSwitched';
export const WORKSPACE_CACHED = 'WorkspaceCached';
export const WORKSPACE_RESTORED = 'WorkspaceRestored';

export interface WorkspaceOpenedEvent extends RuntimeEvent {
  type: typeof WORKSPACE_OPENED;
  payload: { workspaceId: string; workspaceType: string };
}

export interface WorkspaceClosedEvent extends RuntimeEvent {
  type: typeof WORKSPACE_CLOSED;
  payload: { workspaceId: string; snapshot: Record<string, unknown> | null };
}

export interface WorkspaceSwitchedEvent extends RuntimeEvent {
  type: typeof WORKSPACE_SWITCHED;
  payload: { fromWorkspaceId: string | null; toWorkspaceId: string; transitionType: string };
}

export interface WorkspaceCachedEvent extends RuntimeEvent {
  type: typeof WORKSPACE_CACHED;
  payload: { workspaceId: string; snapshot: Record<string, unknown> };
}

export interface WorkspaceRestoredEvent extends RuntimeEvent {
  type: typeof WORKSPACE_RESTORED;
  payload: { workspaceId: string; snapshot: Record<string, unknown> | null };
}

// ─── Navigation Events ────────────────────────────────────────────────────────

export const NAVIGATION_REQUESTED = 'NavigationRequested';
export const NAVIGATION_COMPLETED = 'NavigationCompleted';
export const NAVIGATION_BACK = 'NavigationBack';
export const NAVIGATION_FORWARD = 'NavigationForward';

export interface NavigationRequestedEvent extends RuntimeEvent {
  type: typeof NAVIGATION_REQUESTED;
  payload: { target: string; source: string };
}

export interface NavigationCompletedEvent extends RuntimeEvent {
  type: typeof NAVIGATION_COMPLETED;
  payload: { route: string; workspaceId: string };
}

export interface NavigationBackEvent extends RuntimeEvent {
  type: typeof NAVIGATION_BACK;
  payload: { fromRoute: string; toRoute: string };
}

export interface NavigationForwardEvent extends RuntimeEvent {
  type: typeof NAVIGATION_FORWARD;
  payload: { fromRoute: string; toRoute: string };
}

// ─── Intelligence Events ──────────────────────────────────────────────────────

export const INSIGHT_GENERATED = 'InsightGenerated';
export const INSIGHT_ACCEPTED = 'InsightAccepted';
export const INSIGHT_DISMISSED = 'InsightDismissed';
export const INSIGHT_ESCALATED = 'InsightEscalated';

export interface InsightGeneratedEvent extends RuntimeEvent {
  type: typeof INSIGHT_GENERATED;
  payload: { insightId: string; tier: 'passive' | 'investigative' | 'executive' };
}

export interface InsightAcceptedEvent extends RuntimeEvent {
  type: typeof INSIGHT_ACCEPTED;
  payload: { insightId: string; actionTaken: string };
}

export interface InsightDismissedEvent extends RuntimeEvent {
  type: typeof INSIGHT_DISMISSED;
  payload: { insightId: string; reason: string };
}

export interface InsightEscalatedEvent extends RuntimeEvent {
  type: typeof INSIGHT_ESCALATED;
  payload: { insightId: string; severity: 'warning' | 'critical' };
}

// ─── Graph Events ─────────────────────────────────────────────────────────────

export const GRAPH_NODE_SELECTED = 'GraphNodeSelected';
export const GRAPH_OVERLAY_OPENED = 'GraphOverlayOpened';
export const GRAPH_OVERLAY_CLOSED = 'GraphOverlayClosed';

export interface GraphNodeSelectedEvent extends RuntimeEvent {
  type: typeof GRAPH_NODE_SELECTED;
  payload: { nodeId: string; nodeType: string; relationships: unknown[] };
}

export interface GraphOverlayOpenedEvent extends RuntimeEvent {
  type: typeof GRAPH_OVERLAY_OPENED;
  payload: { scope: Record<string, unknown>; layout: string };
}

export interface GraphOverlayClosedEvent extends RuntimeEvent {
  type: typeof GRAPH_OVERLAY_CLOSED;
  payload: { reason: string };
}

// ─── Command Events ───────────────────────────────────────────────────────────

export const COMMAND_EXECUTED = 'CommandExecuted';
export const COMMAND_FAILED = 'CommandFailed';
export const COMMAND_PALETTE_OPENED = 'CommandPaletteOpened';
export const COMMAND_PALETTE_CLOSED = 'CommandPaletteClosed';

export interface CommandExecutedEvent extends RuntimeEvent {
  type: typeof COMMAND_EXECUTED;
  payload: { commandId: string; input: string; result: unknown };
}

export interface CommandFailedEvent extends RuntimeEvent {
  type: typeof COMMAND_FAILED;
  payload: { commandId: string; input: string; error: string };
}

export interface CommandPaletteOpenedEvent extends RuntimeEvent {
  type: typeof COMMAND_PALETTE_OPENED;
  payload: { trigger: string };
}

export interface CommandPaletteClosedEvent extends RuntimeEvent {
  type: typeof COMMAND_PALETTE_CLOSED;
  payload: { reason: string };
}

// ─── Unions ───────────────────────────────────────────────────────────────────

export type SelectionEvent =
  | SelectionChangedEvent
  | SelectionClearedEvent
  | SelectionHighlightedEvent;

export type TimelineEvent =
  | TimelineChangedEvent
  | TimelineGranularityChangedEvent
  | TimelineScrubbedEvent;

export type WorkspaceEvent =
  | WorkspaceOpenedEvent
  | WorkspaceClosedEvent
  | WorkspaceSwitchedEvent
  | WorkspaceCachedEvent
  | WorkspaceRestoredEvent;

export type NavigationEvent =
  | NavigationRequestedEvent
  | NavigationCompletedEvent
  | NavigationBackEvent
  | NavigationForwardEvent;

export type IntelligenceEvent =
  | InsightGeneratedEvent
  | InsightAcceptedEvent
  | InsightDismissedEvent
  | InsightEscalatedEvent;

export type GraphEvent =
  | GraphNodeSelectedEvent
  | GraphOverlayOpenedEvent
  | GraphOverlayClosedEvent;

export type CommandEvent =
  | CommandExecutedEvent
  | CommandFailedEvent
  | CommandPaletteOpenedEvent
  | CommandPaletteClosedEvent;

export type RuntimeAllEvent =
  | SelectionEvent
  | TimelineEvent
  | WorkspaceEvent
  | NavigationEvent
  | IntelligenceEvent
  | GraphEvent
  | CommandEvent;

// ─── EventBus Interface ───────────────────────────────────────────────────────

export interface EventSubscriber<T extends RuntimeEvent> {
  (event: T): void;
}

export interface EventUnsubscribe {
  (): void;
}

export interface RuntimeEventBus {
  /** Publish an event to all matching subscribers synchronously. Error-isolated. */
  publish<T extends RuntimeEvent>(event: T): void;

  /** Subscribe to events of a specific type. Returns unsubscribe function. */
  subscribe<T extends RuntimeEvent>(
    eventType: T['type'],
    handler: EventSubscriber<T>,
  ): EventUnsubscribe;

  /** Subscribe to all events (for logging/debugging). Returns unsubscribe function. */
  subscribeAll(handler: EventSubscriber<RuntimeAllEvent>): EventUnsubscribe;

  /** Get a debounced publisher that throttles repeated events of the same type. */
  debouncedPublish<T extends RuntimeEvent>(
    eventType: T['type'],
    ms: number,
  ): (payload: T['payload']) => void;
}

// ─── Implementation ───────────────────────────────────────────────────────────

class EventBus implements RuntimeEventBus {
  private subscribers = new Map<string, Set<EventSubscriber<RuntimeEvent>>>();
  private allListeners = new Set<EventSubscriber<RuntimeAllEvent>>();
  private debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

  publish<T extends RuntimeEvent>(event: T): void {
    const typeSubs = this.subscribers.get(event.type);
    if (typeSubs) {
      for (const handler of typeSubs) {
        try {
          handler(event);
        } catch (err) {
          console.error(`[EventBus] Subscriber error for "${event.type}":`, err);
        }
      }
    }
    // Notify all-listener subscribers
    for (const handler of this.allListeners) {
      try {
        handler(event as unknown as RuntimeAllEvent);
      } catch (err) {
        console.error(`[EventBus] All-subscriber error for "${event.type}":`, err);
      }
    }
  }

  subscribe<T extends RuntimeEvent>(
    eventType: T['type'],
    handler: EventSubscriber<T>,
  ): EventUnsubscribe {
    if (!this.subscribers.has(eventType)) {
      this.subscribers.set(eventType, new Set());
    }
    this.subscribers.get(eventType)!.add(handler as EventSubscriber<RuntimeEvent>);
    return () => {
      this.subscribers.get(eventType)?.delete(handler as EventSubscriber<RuntimeEvent>);
    };
  }

  subscribeAll(handler: EventSubscriber<RuntimeAllEvent>): EventUnsubscribe {
    this.allListeners.add(handler as EventSubscriber<RuntimeEvent>);
    return () => {
      this.allListeners.delete(handler as EventSubscriber<RuntimeEvent>);
    };
  }

  debouncedPublish<T extends RuntimeEvent>(
    eventType: T['type'],
    ms: number,
  ): (payload: T['payload']) => void {
    return (payload: T['payload']) => {
      const key = `${eventType}-debounce`;
      clearTimeout(this.debounceTimers.get(key));
      this.debounceTimers.set(
        key,
        setTimeout(() => {
          this.publish({
            type: eventType,
            timestamp: Date.now(),
            source: 'runtime',
            payload,
          } as T);
        }, ms),
      );
    };
  }

  reset(): void {
    this.subscribers.clear();
    this.allListeners.clear();
    this.debounceTimers.forEach(t => clearTimeout(t));
    this.debounceTimers.clear();
  }
}

// ─── Singleton ────────────────────────────────────────────────────────────────

const _bus = new EventBus();

export const runtimeEventBus = _bus;

export function resetRuntimeEventBus(): void {
  _bus.reset();
}
