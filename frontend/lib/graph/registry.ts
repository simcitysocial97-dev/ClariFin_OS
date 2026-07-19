/**
 * Graph Registry - Stage 4B Financial Graph Runtime
 *
 * Central registry for all workspace graph adapters.
 * Adapters register themselves, and the runtime queries them
 * to build the complete financial graph.
 *
 * Architecture: Adapter → Registry → Runtime
 */

import type { GraphAdapter, GraphResult, GraphMetadata } from './types';
import { mergeGraphResults } from './adapter';

// ===== Registry Error Types =====
export class RegistryError extends Error {
  constructor(message: string) {
    super(`[GraphRegistry] ${message}`);
    this.name = 'RegistryError';
  }
}

export class AdapterNotFoundError extends RegistryError {
  constructor(name: string) {
    super(`Adapter '${name}' not found in registry`);
    this.name = 'AdapterNotFoundError';
  }
}

export class AdapterAlreadyRegisteredError extends RegistryError {
  constructor(name: string) {
    super(`Adapter '${name}' is already registered`);
    this.name = 'AdapterAlreadyRegisteredError';
  }
}

// ===== Registry =====
/**
 * Singleton registry for graph adapters.
 * Manages registration, lookup, and bulk operations.
 */
export class GraphRegistry {
  private static instance: GraphRegistry;
  private adapters: Map<string, GraphAdapter<unknown>> = new Map();

  private constructor() {
    // Private constructor for singleton pattern
  }

  /**
   * Get the singleton instance
   */
  static getInstance(): GraphRegistry {
    if (!GraphRegistry.instance) {
      GraphRegistry.instance = new GraphRegistry();
    }
    return GraphRegistry.instance;
  }

  /**
   * Reset the singleton instance (useful for testing)
   */
  static resetInstance(): void {
    GraphRegistry.instance = new GraphRegistry();
  }

  /**
   * Register a new adapter
   * Throws if an adapter with the same name already exists
   */
  register<T>(adapter: GraphAdapter<T>): void {
    if (this.adapters.has(adapter.name)) {
      throw new AdapterAlreadyRegisteredError(adapter.name);
    }
    this.adapters.set(adapter.name, adapter as GraphAdapter<unknown>);
  }

  /**
   * Register an adapter, replacing any existing one with the same name
   */
  registerOrReplace<T>(adapter: GraphAdapter<T>): void {
    this.adapters.set(adapter.name, adapter as GraphAdapter<unknown>);
  }

  /**
   * Unregister an adapter by name
   */
  unregister(name: string): boolean {
    return this.adapters.delete(name);
  }

  /**
   * Get a registered adapter by name
   */
  get<T = unknown>(name: string): GraphAdapter<T> {
    const adapter = this.adapters.get(name);
    if (!adapter) {
      throw new AdapterNotFoundError(name);
    }
    return adapter as GraphAdapter<T>;
  }

  /**
   * Check if an adapter is registered
   */
  has(name: string): boolean {
    return this.adapters.has(name);
  }

  /**
   * Get all registered adapter names
   */
  getAdapterNames(): string[] {
    return Array.from(this.adapters.keys());
  }

  /**
   * Get all registered adapters
   */
  getAll(): GraphAdapter<unknown>[] {
    return Array.from(this.adapters.values());
  }

  /**
   * Get the count of registered adapters
   */
  get count(): number {
    return this.adapters.size;
  }

  /**
   * Build a complete GraphResult from all registered adapters
   * Each adapter's ViewModel must be provided via the viewModels map
   */
  buildAll(viewModels: Record<string, unknown>): GraphResult {
    const results: GraphResult[] = [];

    for (const [name, adapter] of this.adapters) {
      const viewModel = viewModels[name];
      if (viewModel !== undefined) {
        results.push(adapter.export(viewModel));
      }
      // Skip adapters with no ViewModel provided
    }

    if (results.length === 0) {
      return {
        nodes: [],
        edges: [],
        metadata: {
          node_count: 0,
          edge_count: 0,
          nodes_by_type: {} as Record<string, number>,
          edges_by_type: {} as Record<string, number>,
          workspaces: [],
          built_at: new Date().toISOString(),
          version: '1.0.0',
        },
      };
    }

    return mergeGraphResults(results);
  }

  /**
   * Build GraphResult for a specific adapter by name
   */
  buildOne<T>(name: string, viewModel: T): GraphResult {
    const adapter = this.get<T>(name);
    return adapter.export(viewModel);
  }

  /**
   * Get combined metadata from all registered adapters
   * (without building the full graph)
   */
  getCombinedMetadata(viewModels: Record<string, unknown>): GraphMetadata {
    const result = this.buildAll(viewModels);
    return result.metadata;
  }

  /**
   * Clear all registered adapters
   */
  clear(): void {
    this.adapters.clear();
  }
}

// ===== Convenience Export =====
/** Default registry instance */
export const graphRegistry = GraphRegistry.getInstance();