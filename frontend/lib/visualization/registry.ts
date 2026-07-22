/**
 * Visualization Registry - Stage 8C Financial OS Visual System
 *
 * Maps surface types to visualization components.
 * Makes visualization pluggable.
 */

import type { SurfaceType } from '../workspace/workspace-registry';

// ===== Visualization Component Types =====
export type VisualizationComponent =
  | 'MoneyGraph'
  | 'InvestigationTable'
  | 'TimelineEngine'
  | 'SankeyEngine'
  | 'AllocationMatrix'
  | 'ScenarioEngine'
  | 'WaterfallEngine'
  | 'EvidenceTree'
  | 'ConfigurationSurface'
  | 'MetricsOverview'
  | 'RelationshipExplorer'
  | 'CreditTimeline'
  | 'DebtWaterfall'
  | 'CapitalTimeline'
  | 'MatchingWorkspace';

// ===== Visualization Registration =====
export interface VisualizationRegistration {
  surfaceType: SurfaceType;
  component: VisualizationComponent;
  description: string;
}

// ===== Visualization Registry =====
export class VisualizationRegistry {
  private static instance: VisualizationRegistry;
  private visualizations: Map<SurfaceType, VisualizationRegistration> = new Map();

  private constructor() {
    this.registerDefaultVisualizations();
  }

  static getInstance(): VisualizationRegistry {
    if (!VisualizationRegistry.instance) {
      VisualizationRegistry.instance = new VisualizationRegistry();
    }
    return VisualizationRegistry.instance;
  }

  register(registration: VisualizationRegistration): void {
    this.visualizations.set(registration.surfaceType, registration);
  }

  get(surfaceType: SurfaceType): VisualizationRegistration | undefined {
    return this.visualizations.get(surfaceType);
  }

  getAll(): VisualizationRegistration[] {
    return Array.from(this.visualizations.values());
  }

  private registerDefaultVisualizations(): void {
    const registrations: VisualizationRegistration[] = [
      {
        surfaceType: 'GRAPH',
        component: 'MoneyGraph',
        description: 'Interactive financial graph with node clustering and edge highlighting',
      },
      {
        surfaceType: 'TABLE',
        component: 'InvestigationTable',
        description: 'Transaction investigation table with evidence and filtering',
      },
      {
        surfaceType: 'TIMELINE',
        component: 'TimelineEngine',
        description: 'Behaviour and forecast timeline visualization',
      },
      {
        surfaceType: 'SANKEY',
        component: 'SankeyEngine',
        description: 'Cashflow and money flow sankey diagram',
      },
      {
        surfaceType: 'MATRIX',
        component: 'AllocationMatrix',
        description: 'Portfolio and asset allocation matrix',
      },
      {
        surfaceType: 'SIMULATION',
        component: 'ScenarioEngine',
        description: 'Forecast and scenario simulation visualization',
      },
      {
        surfaceType: 'CONFIGURATION',
        component: 'ConfigurationSurface',
        description: 'Settings and configuration surface',
      },
    ];

    for (const registration of registrations) {
      this.visualizations.set(registration.surfaceType, registration);
    }
  }
}

// ===== Convenience Export =====
export const visualizationRegistry = VisualizationRegistry.getInstance();