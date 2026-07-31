import { ContextRuntime } from './workspace/ContextRuntime';
import { Context } from '../models/types';


export class ContextNavigation {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public navigate(
    contextId: string,
    path: string,
    params: Record<string, unknown> = {}
  ): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const updatedContext = this.runtime['updateContext'](contextId, {
      navigationState: { path, params },
    });

    this.runtime['recordEvent']('navigation.updated', contextId, {
      path,
      params,
    });

    return this.runtime['cloneContext'](updatedContext);
  }

  public getNavigationState(contextId: string): { path: string; params: Record<string, unknown> } {
    return this.runtime.navigation(contextId);
  }
}