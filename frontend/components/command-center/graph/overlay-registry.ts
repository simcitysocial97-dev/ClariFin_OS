/**
 * Overlay Registry - Stage 8E-B Command Center
 *
 * Plugin registry for graph overlays.
 * Each overlay is a self-contained component that can be toggled.
 */

import type { GraphNode, GraphEdge } from '@/lib/graph';

// ===== Overlay Types =====
export type OverlayType =
  | 'money-flow'
  | 'selection-halo'
  | 'confidence-ring'
  | 'risk-pulse'
  | 'forecast-edge'
  | 'evidence-count'
  | 'related-entity-count';

// ===== Overlay Definition =====
export interface OverlayDefinition {
  id: OverlayType;
  label: string;
  description: string;
  defaultVisible: boolean;
}

// ===== Overlay Context =====
export interface OverlayContext {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodeId: string | null;
  hoveredNodeId: string | null;
  layout: 'force' | 'tree' | 'radial' | 'timeline' | 'grid';
}

// ===== Overlay Component Props =====
export interface OverlayComponentProps {
  context: OverlayContext;
  visible: boolean;
}

// ===== Overlay Registry =====
export class OverlayRegistry {
  private static instance: OverlayRegistry;
  private overlays: Map<OverlayType, OverlayDefinition> = new Map();
  private visibility: Map<OverlayType, boolean> = new Map();

  private constructor() {
    this.registerDefaultOverlays();
  }

  static getInstance(): OverlayRegistry {
    if (!OverlayRegistry.instance) {
      OverlayRegistry.instance = new OverlayRegistry();
    }
    return OverlayRegistry.instance;
  }

  register(overlay: OverlayDefinition): void {
    this.overlays.set(overlay.id, overlay);
    if (!this.visibility.has(overlay.id)) {
      this.visibility.set(overlay.id, overlay.defaultVisible);
    }
  }

  get(id: OverlayType): OverlayDefinition | undefined {
    return this.overlays.get(id);
  }

  getAll(): OverlayDefinition[] {
    return Array.from(this.overlays.values());
  }

  isVisible(id: OverlayType): boolean {
    return this.visibility.get(id) ?? false;
  }

  setVisible(id: OverlayType, visible: boolean): void {
    this.visibility.set(id, visible);
  }

  toggle(id: OverlayType): void {
    const current = this.visibility.get(id) ?? false;
    this.visibility.set(id, !current);
  }

  private registerDefaultOverlays(): void {
    const defaultOverlays: OverlayDefinition[] = [
      {
        id: 'money-flow',
        label: 'Money Flow',
        description: 'Shows money flow direction and amount',
        defaultVisible: true,
      },
      {
        id: 'selection-halo',
        label: 'Selection Halo',
        description: 'Highlights selected nodes',
        defaultVisible: true,
      },
      {
        id: 'confidence-ring',
        label: 'Confidence Ring',
        description: 'Shows confidence level around nodes',
        defaultVisible: false,
      },
      {
        id: 'risk-pulse',
        label: 'Risk Pulse',
        description: 'Pulses on high-risk nodes',
        defaultVisible: false,
      },
      {
        id: 'forecast-edge',
        label: 'Forecast Edge',
        description: 'Shows forecast projection edges',
        defaultVisible: true,
      },
      {
        id: 'evidence-count',
        label: 'Evidence Count',
        description: 'Shows evidence count on nodes',
        defaultVisible: false,
      },
      {
        id: 'related-entity-count',
        label: 'Related Entity Count',
        description: 'Shows count of related entities',
        defaultVisible: false,
      },
    ];

    for (const overlay of defaultOverlays) {
      this.register(overlay);
    }
  }
}

// ===== Convenience Export =====
export const overlayRegistry = OverlayRegistry.getInstance();