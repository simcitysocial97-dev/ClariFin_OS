/**
 * Overlay Manager - Stage 8F Financial OS Interaction Layer
 *
 * Central overlay registry for the OS.
 * No overlay logic inside graph components.
 */

import type { OverlayType } from '@/lib/interaction/interaction-types';

// ===== Overlay Definition =====
export interface OverlayDefinition {
  id: OverlayType;
  label: string;
  description: string;
  visible: boolean;
}

// ===== Overlay Manager =====
class OverlayManager {
  private overlays: Map<OverlayType, OverlayDefinition> = new Map();
  private listeners: Array<(overlays: OverlayDefinition[]) => void> = [];

  // ===== Registration =====
  /**
   * Register an overlay
   */
  register(overlay: OverlayDefinition): void {
    this.overlays.set(overlay.id, overlay);
    this.notify();
  }

  /**
   * Unregister an overlay
   */
  unregister(id: OverlayType): boolean {
    const result = this.overlays.delete(id);
    this.notify();
    return result;
  }

  /**
   * Get an overlay by ID
   */
  get(id: OverlayType): OverlayDefinition | undefined {
    return this.overlays.get(id);
  }

  /**
   * Get all overlays
   */
  getAll(): OverlayDefinition[] {
    return Array.from(this.overlays.values());
  }

  // ===== Visibility =====
  /**
   * Check if an overlay is visible
   */
  isVisible(id: OverlayType): boolean {
    return this.overlays.get(id)?.visible ?? false;
  }

  /**
   * Set overlay visibility
   */
  setVisible(id: OverlayType, visible: boolean): void {
    const overlay = this.overlays.get(id);
    if (overlay) {
      overlay.visible = visible;
      this.notify();
    }
  }

  /**
   * Toggle overlay visibility
   */
  toggle(id: OverlayType): void {
    const overlay = this.overlays.get(id);
    if (overlay) {
      overlay.visible = !overlay.visible;
      this.notify();
    }
  }

  // ===== Subscription =====
  /**
   * Subscribe to overlay changes
   */
  subscribe(listener: (overlays: OverlayDefinition[]) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  // ===== Private Methods =====
  private notify(): void {
    for (const listener of this.listeners) {
      listener(this.getAll());
    }
  }

  // ===== Reset =====
  /**
   * Reset the overlay manager
   */
  reset(): void {
    this.overlays.clear();
    this.notify();
  }
}

// ===== Singleton Export =====
export const overlayManager = new OverlayManager();

// ===== Default Overlays =====
/**
 * Initialize default overlays
 */
export function initDefaultOverlays(): void {
  const defaultOverlays: OverlayDefinition[] = [
    {
      id: 'money-flow',
      label: 'Money Flow',
      description: 'Shows money flow direction and amount',
      visible: true,
    },
    {
      id: 'risk',
      label: 'Risk',
      description: 'Shows risk indicators on nodes',
      visible: false,
    },
    {
      id: 'confidence',
      label: 'Confidence',
      description: 'Shows confidence level around nodes',
      visible: false,
    },
    {
      id: 'selection',
      label: 'Selection',
      description: 'Highlights selected nodes',
      visible: true,
    },
    {
      id: 'evidence',
      label: 'Evidence',
      description: 'Shows evidence count on nodes',
      visible: false,
    },
    {
      id: 'simulation',
      label: 'Simulation',
      description: 'Shows simulation projection edges',
      visible: true,
    },
    {
      id: 'forecast',
      label: 'Forecast',
      description: 'Shows forecast data',
      visible: false,
    },
    {
      id: 'dependencies',
      label: 'Dependencies',
      description: 'Shows dependency relationships',
      visible: false,
    },
    {
      id: 'ownership',
      label: 'Ownership',
      description: 'Shows ownership structure',
      visible: false,
    },
  ];

  for (const overlay of defaultOverlays) {
    overlayManager.register(overlay);
  }
}