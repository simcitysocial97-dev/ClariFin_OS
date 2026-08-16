import { ContextRuntime } from './workspace/ContextRuntime';
import { Context } from '../models/types';


export class ContextFocus {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public focusObject(contextId: string, object: { id: string; type: string }): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const updatedContext = this.runtime['updateContext'](contextId, {
      focusedObject: object,
    });

    this.runtime['recordEvent']('focus.updated', contextId, { object });
    return this.runtime['cloneContext'](updatedContext);
  }

  public clearFocus(contextId: string): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const updatedContext = this.runtime['updateContext'](contextId, {
      focusedObject: undefined,
    });

    this.runtime['recordEvent']('focus.cleared', contextId, {});
    return this.runtime['cloneContext'](updatedContext);
  }

  public getFocus(contextId: string): { id: string; type: string } | undefined {
    return this.runtime.focus(contextId);
  }
}