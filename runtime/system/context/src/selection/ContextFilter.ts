import { ContextRuntime } from './workspace/ContextRuntime';
import { Context } from '../models/types';


export class ContextFilter {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public applyFilter(
    contextId: string,
    filter: { id: string; type: string; value: unknown }
  ): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const context = this.runtime['contexts'].get(contextId)!;
    const updatedFilters = [...context.appliedFilters, filter];
    const updatedContext = this.runtime['updateContext'](contextId, {
      appliedFilters: updatedFilters,
    });

    this.runtime['recordEvent']('filter.applied', contextId, { filter });
    return this.runtime['cloneContext'](updatedContext);
  }

  public removeFilter(contextId: string, filterId: string): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const context = this.runtime['contexts'].get(contextId)!;
    const updatedFilters = context.appliedFilters.filter(f => f.id !== filterId);
    const updatedContext = this.runtime['updateContext'](contextId, {
      appliedFilters: updatedFilters,
    });

    this.runtime['recordEvent']('filter.removed', contextId, { filterId });
    return this.runtime['cloneContext'](updatedContext);
  }

  public clearFilters(contextId: string): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const updatedContext = this.runtime['updateContext'](contextId, {
      appliedFilters: [],
    });

    this.runtime['recordEvent']('filters.cleared', contextId, {});
    return this.runtime['cloneContext'](updatedContext);
  }

  public getFilters(contextId: string): Array<{ id: string; type: string; value: unknown }> {
    return this.runtime.filters(contextId);
  }
}