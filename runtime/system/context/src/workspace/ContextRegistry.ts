import { Context, ContextType } from '../models/types';
import { ContextRuntime } from './workspace/ContextRuntime';


export class ContextRegistry {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public registerContext(
    name: string,
    type: ContextType,
    owner: string,
    workspace: string,
    metadata: Record<string, unknown> = {}
  ): Context {
    return this.runtime.createContext(name, type, owner, workspace, metadata);
  }

  public unregisterContext(contextId: string): void {
    this.runtime.destroyContext(contextId);
  }

  public listContexts(): Context[] {
    return Array.from(this.runtime['contexts'].values()).map(ctx => this.runtime['cloneContext'](ctx));
  }

  public getContext(contextId: string): Context | undefined {
    const context = this.runtime['contexts'].get(contextId);
    return context ? this.runtime['cloneContext'](context) : undefined;
  }

  public contextExists(contextId: string): boolean {
    return this.runtime['contexts'].has(contextId);
  }
}