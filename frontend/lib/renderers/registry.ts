/**
 * Renderer Registry — Architecture Section 7.5
 *
 * Maps Financial Object types to their renderer implementations.
 * Each renderer mode is a pure presentational component that receives
 * a RenderableViewModel and renders the appropriate UI.
 *
 * Usage:
 *   const registry = new RendererRegistry();
 *   registry.register('transaction', 'card', TransactionCardRenderer);
 *   const CardRenderer = registry.get('transaction', 'card');
 */

import type {
  RendererMode,
  RendererComponent,
  RegisteredRenderer,
  DensityLevel,
} from './types';

// ===== Renderer Registry =====
export class RendererRegistry {
  private readonly _registry = new Map<
    string,
    Map<RendererMode, RegisteredRenderer>
  >();

  /**
   * Register a renderer for a specific object type and mode.
   */
  register<TData = unknown>(
    objectType: string,
    mode: RendererMode,
    component: RendererComponent<TData>,
    options?: { defaultDensity?: DensityLevel },
  ): void {
    let typeMap = this._registry.get(objectType);
    if (!typeMap) {
      typeMap = new Map<RendererMode, RegisteredRenderer>();
      this._registry.set(objectType, typeMap);
    }
    typeMap.set(mode, {
      objectType,
      mode,
      component: component as RendererComponent<unknown>,
      defaultDensity: options?.defaultDensity ?? 'comfortable',
    });
  }

  /**
   * Get the renderer for a specific object type and mode.
   */
  get<TData = unknown>(objectType: string, mode: RendererMode): RendererComponent<TData> | null {
    const typeMap = this._registry.get(objectType);
    if (!typeMap) return null;
    const entry = typeMap.get(mode);
    if (!entry) return null;
    return entry.component as RendererComponent<TData>;
  }

  /**
   * Check if a renderer exists for the given type and mode.
   */
  has(objectType: string, mode: RendererMode): boolean {
    const typeMap = this._registry.get(objectType);
    if (!typeMap) return false;
    return typeMap.has(mode);
  }

  /**
   * Get all registered modes for an object type.
   */
  getModes(objectType: string): RendererMode[] {
    const typeMap = this._registry.get(objectType);
    if (!typeMap) return [];
    return Array.from(typeMap.keys()) as RendererMode[];
  }

  /**
   * Get the default density for a registered renderer.
   */
  getDefaultDensity(objectType: string, mode: RendererMode): DensityLevel {
    const typeMap = this._registry.get(objectType);
    const entry = typeMap?.get(mode);
    return entry?.defaultDensity ?? 'comfortable';
  }

  /**
   * Get all registered object types.
   */
  getObjectTypes(): string[] {
    return Array.from(this._registry.keys());
  }

  /**
   * Get all registered renderers (flattened).
   */
  getAll(): RegisteredRenderer[] {
    const result: RegisteredRenderer[] = [];
    for (const typeMap of this._registry.values()) {
      for (const entry of typeMap.values()) {
        result.push(entry);
      }
    }
    return result;
  }

  /**
   * Clear all registrations.
   */
  clear(): void {
    this._registry.clear();
  }
}

// ===== Singleton Instance =====
let _instance: RendererRegistry | null = null;

export function getRendererRegistry(): RendererRegistry {
  if (!_instance) {
    _instance = new RendererRegistry();
  }
  return _instance;
}

/**
 * Reset the singleton registry (mainly for testing).
 */
export function resetRendererRegistry(): void {
  _instance = new RendererRegistry();
}
