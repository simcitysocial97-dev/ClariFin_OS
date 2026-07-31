import { ContextRuntime } from './workspace/ContextRuntime';
import { Context, ContextType } from '../models/types';


export class ContextSession {
  private runtime: ContextRuntime;
  private currentContextId: string | null;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
    this.currentContextId = null;
  }

  public startSession(
    name: string,
    type: ContextType,
    owner: string,
    workspace: string,
    metadata: Record<string, unknown> = {}
  ): Context {
    const context = this.runtime.createContext(name, type, owner, workspace, metadata);
    this.currentContextId = context.id;
    return context;
  }

  public endSession(): void {
    if (this.currentContextId) {
      this.runtime.destroyContext(this.currentContextId);
      this.currentContextId = null;
    }
  }

  public getCurrentContext(): Context | null {
    if (!this.currentContextId) return null;
    const context = this.runtime['contexts'].get(this.currentContextId);
    return context ? this.runtime['cloneContext'](context) : null;
  }

  public switchContext(contextId: string): Context {
    if (!this.runtime['contexts'].has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }
    this.currentContextId = contextId;
    return this.getCurrentContext()!;
  }

  public snapshotCurrentContext() {
    if (!this.currentContextId) {
      throw new Error('No active context');
    }
    return this.runtime.snapshot(this.currentContextId);
  }
}