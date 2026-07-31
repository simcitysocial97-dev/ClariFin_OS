import { ContextRuntime } from './workspace/ContextRuntime';
import { Context, ContextType, ContextSnapshot, ContextEvent, Workspace } from '../models/types';


export class ContextManager {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public createContext(
    name: string,
    type: ContextType,
    owner: string,
    workspace: string,
    metadata: Record<string, unknown> = {}
  ): Context {
    return this.runtime.createContext(name, type, owner, workspace, metadata);
  }

  public destroyContext(contextId: string): void {
    this.runtime.destroyContext(contextId);
  }

  public activateContext(contextId: string): Context {
    return this.runtime.activateContext(contextId);
  }

  public snapshot(contextId: string): ContextSnapshot {
    return this.runtime.snapshot(contextId);
  }

  public restore(snapshotId: string): Context {
    return this.runtime.restore(snapshotId);
  }

  public getHistory(contextId: string): ContextEvent[] {
    return this.runtime.history(contextId);
  }

  public getWorkspace(workspaceId: string): Workspace {
    return this.runtime.workspace(workspaceId);
  }

  public getSelection(contextId: string): Array<{ id: string; type: string }> {
    return this.runtime.selection(contextId);
  }

  public getFocus(contextId: string): { id: string; type: string } | undefined {
    return this.runtime.focus(contextId);
  }

  public getNavigation(contextId: string): { path: string; params: Record<string, unknown> } {
    return this.runtime.navigation(contextId);
  }

  public getFilters(contextId: string): Array<{ id: string; type: string; value: unknown }> {
    return this.runtime.filters(contextId);
  }

  public getComparison(contextId: string): { comparedContexts: string[]; comparisonType: string } | undefined {
    return this.runtime.compare(contextId);
  }

  public serializeContext(contextId: string): string {
    return this.runtime.serialize(contextId);
  }

  public deserializeContext(serializedContext: string): Context {
    return this.runtime.deserialize(serializedContext);
  }

  public validateContext(context: Context): boolean {
    return this.runtime.validate(context);
  }
}