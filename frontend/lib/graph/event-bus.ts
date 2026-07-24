/**
 * Graph Event Bus - Stage 4B Financial Graph Runtime
 *
 * Typed event system for the Financial Graph Runtime.
 * Enables decoupled communication between graph components.
 *
 * Architecture: Component → Event Bus → Subscribers
 */

import type { GraphEventType, GraphEvent } from './types';

// ===== Event Handler Types =====
export type GraphEventHandler<T = unknown> = (event: GraphEvent & { payload: T }) => void;

// ===== Subscription =====
export interface Subscription {
  /** Unique subscription ID */
  id: string;
  /** Event type being subscribed to */
  eventType: GraphEventType | '*';
  /** Unsubscribe function */
  unsubscribe: () => void;
}

// ===== Event Bus =====
/**
 * Typed event bus for graph events.
 * Supports wildcard subscriptions and per-type handlers.
 */
export class GraphEventBus {
  private handlers: Map<GraphEventType | '*', Map<string, GraphEventHandler>> = new Map();
  private subscriptionCounter = 0;
  private eventLog: GraphEvent[] = [];
  private maxLogSize: number;

  constructor(maxLogSize = 1000) {
    this.maxLogSize = maxLogSize;
  }

  /**
   * Subscribe to a specific event type or all events ('*')
   */
  subscribe<T = unknown>(
    eventType: GraphEventType | '*',
    handler: GraphEventHandler<T>,
  ): Subscription {
    const id = `sub_${++this.subscriptionCounter}`;

    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Map());
    }

    const typeHandlers = this.handlers.get(eventType)!;
    typeHandlers.set(id, handler as GraphEventHandler);

    return {
      id,
      eventType,
      unsubscribe: () => {
        const handlers = this.handlers.get(eventType);
        if (handlers) {
          handlers.delete(id);
          if (handlers.size === 0) {
            this.handlers.delete(eventType);
          }
        }
      },
    };
  }

  /**
   * Subscribe to a specific event type, automatically unsubscribing after first event
   */
  subscribeOnce<T = unknown>(
    eventType: GraphEventType | '*',
    handler: GraphEventHandler<T>,
  ): Subscription {
    const wrappedHandler: GraphEventHandler<T> = (event) => {
      handler(event);
      sub.unsubscribe();
    };

    const sub = this.subscribe(eventType, wrappedHandler);
    return sub;
  }

  /**
   * Emit an event to all subscribers
   */
  emit<T = unknown>(
    type: GraphEventType,
    payload: T,
    source: string,
  ): void {
    const event: GraphEvent = {
      type,
      payload,
      timestamp: new Date().toISOString(),
      source,
    };

    // Log the event
    this.eventLog.push(event);
    if (this.eventLog.length > this.maxLogSize) {
      this.eventLog.shift();
    }

    // Notify type-specific handlers
    const typeHandlers = this.handlers.get(type);
    if (typeHandlers) {
      for (const handler of typeHandlers.values()) {
        try {
          handler(event as GraphEvent & { payload: T });
        } catch (error) {
          console.error(`[GraphEventBus] Error in handler for '${type}':`, error);
        }
      }
    }

    // Notify wildcard handlers
    const wildcardHandlers = this.handlers.get('*');
    if (wildcardHandlers) {
      for (const handler of wildcardHandlers.values()) {
        try {
          handler(event as GraphEvent & { payload: T });
        } catch (error) {
          console.error(`[GraphEventBus] Error in wildcard handler:`, error);
        }
      }
    }
  }

  /**
   * Unsubscribe a specific handler
   */
  unsubscribe(id: string): void {
    for (const [, handlers] of this.handlers) {
      if (handlers.has(id)) {
        handlers.delete(id);
        return;
      }
    }
  }

  /**
   * Remove all subscriptions for a specific event type
   */
  clearEventType(eventType: GraphEventType | '*'): void {
    this.handlers.delete(eventType);
  }

  /**
   * Remove all subscriptions
   */
  clearAll(): void {
    this.handlers.clear();
  }

  /**
   * Get the number of subscribers for a specific event type (or total)
   */
  subscriberCount(eventType?: GraphEventType | '*'): number {
    if (eventType) {
      return this.handlers.get(eventType)?.size ?? 0;
    }
    let count = 0;
    for (const [, handlers] of this.handlers) {
      count += handlers.size;
    }
    return count;
  }

  /**
   * Get the event log (for debugging and explainability)
   */
  getEventLog(limit?: number): GraphEvent[] {
    if (limit && limit > 0) {
      return this.eventLog.slice(-limit);
    }
    return [...this.eventLog];
  }

  /**
   * Clear the event log
   */
  clearEventLog(): void {
    this.eventLog = [];
  }

  /**
   * Get events of a specific type from the log
   */
  getEventsByType(type: GraphEventType): GraphEvent[] {
    return this.eventLog.filter(e => e.type === type);
  }
}

// ===== Convenience Export =====
/** Default event bus instance */
export const graphEventBus = new GraphEventBus();