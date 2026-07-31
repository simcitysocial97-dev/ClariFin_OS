import { ContextRuntime } from './workspace/ContextRuntime';
import { Context } from '../models/types';


export class ContextSelection {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public selectObjects(contextId: string, objects: Array<{ id: string; type: string }>): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const updatedContext = this.runtime['updateContext'](contextId, {
      selectedFinancialObjects: objects,
    });

    this.runtime['recordEvent']('selection.updated', contextId, {
      selectedObjects: objects,
    });

    return this.runtime['cloneContext'](updatedContext);
  }

  public clearSelection(contextId: string): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const updatedContext = this.runtime['updateContext'](contextId, {
      selectedFinancialObjects: [],
    });

    this.runtime['recordEvent']('selection.cleared', contextId, {});
    return this.runtime['cloneContext'](updatedContext);
  }

  public getSelection(contextId: string): Array<{ id: string; type: string }> {
    return this.runtime.selection(contextId);
  }
}