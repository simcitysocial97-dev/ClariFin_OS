import { Context, ContextType, ContextSnapshot, ContextEvent, Workspace } from '../models/types';


export class ContextRuntime {
  private static instance: ContextRuntime;
  private contexts: Map<string, Context>;
  private snapshots: Map<string, ContextSnapshot>;
  private events: ContextEvent[];
  private workspaces: Map<string, Workspace>;
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  private _activeWorkspace: string | null = null;

  private constructor() {
    this.contexts = new Map();
    this.snapshots = new Map();
    this.events = [];
    this.workspaces = new Map();
    this._activeWorkspace = null;
  }

  public static getInstance(): ContextRuntime {
    if (!ContextRuntime.instance) {
      ContextRuntime.instance = new ContextRuntime();
    }
    return ContextRuntime.instance;
  }

  public createContext(
    name: string,
    type: ContextType,
    owner: string,
    workspace: string,
    metadata: Record<string, unknown> = {}
  ): Context {
    const id = this.generateId();
    const now = new Date().toISOString();

    const context: Context = {
      id,
      name,
      type,
      createdTime: now,
      updatedTime: now,
      owner,
      workspace,
      currentTimeScope: { start: now, end: now },
      selectedFinancialObjects: [],
      appliedFilters: [],
      navigationState: { path: '/', params: {} },
      pinnedObjects: [],
      temporaryObjects: [],
      historyStack: [],
      metadata,
      evidenceReferences: [],
      explainabilityReferences: [],
    };

    this.contexts.set(id, context);
    this.recordEvent('context.created', id, { metadata });
    this.addContextToWorkspace(workspace, id);
    return this.cloneContext(context);
  }

  public destroyContext(contextId: string): void {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const context = this.contexts.get(contextId)!;
    this.recordEvent('context.destroyed', contextId, { context });
    this.contexts.delete(contextId);
    this.removeContextFromWorkspace(context.workspace, contextId);
  }

  public activateContext(contextId: string): Context {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }
    const updatedContext = this.updateContext(contextId, { updatedTime: new Date().toISOString() });
    this.recordEvent('context.activated', contextId, { context: updatedContext });
    return this.cloneContext(updatedContext);
  }

  public snapshot(contextId: string): ContextSnapshot {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const context = this.contexts.get(contextId)!;
    const snapshotId = this.generateId();
    const snapshot: ContextSnapshot = {
      id: snapshotId,
      contextId,
      timestamp: new Date().toISOString(),
      state: this.cloneContext(context),
    };

    this.snapshots.set(snapshotId, snapshot);
    this.recordEvent('snapshot.created', contextId, { snapshotId });
    return snapshot;
  }

  public restore(snapshotId: string): Context {
    if (!this.snapshots.has(snapshotId)) {
      throw new Error(`Snapshot ${snapshotId} not found`);
    }

    const snapshot = this.snapshots.get(snapshotId)!;
    const context = this.cloneContext(snapshot.state);
    this.contexts.set(context.id, context);
    this.recordEvent('context.restored', context.id, { snapshotId });
    return this.cloneContext(context);
  }

  public history(contextId: string): ContextEvent[] {
    return this.events.filter(event => event.contextId === contextId);
  }

  public workspace(workspaceId: string): Workspace {
    if (!this.workspaces.has(workspaceId)) {
      throw new Error(`Workspace ${workspaceId} not found`);
    }
    return this.cloneWorkspace(this.workspaces.get(workspaceId)!);
  }

  public selection(contextId: string): Array<{ id: string; type: string }> {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }
    return [...this.contexts.get(contextId)!.selectedFinancialObjects];
  }

  public focus(contextId: string): { id: string; type: string } | undefined {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }
    const ctx = this.contexts.get(contextId)!;
    if (!ctx.focusedObject) return undefined;
    return {
      id: ctx.focusedObject.id || '',
      type: ctx.focusedObject.type || '',
    };
  }

  public navigation(contextId: string): { path: string; params: Record<string, unknown> } {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }
    const ctx = this.contexts.get(contextId)!;
    return { ...ctx.navigationState };
  }

  public filters(contextId: string): Array<{ id: string; type: string; value: unknown }> {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }
    return [...this.contexts.get(contextId)!.appliedFilters];
  }

  public compare(contextId: string): { comparedContexts: string[]; comparisonType: string } | undefined {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }
    const ctx = this.contexts.get(contextId)!;
    if (!ctx.comparisonState) return undefined;
    return {
      comparedContexts: ctx.comparisonState.comparedContexts || [],
      comparisonType: ctx.comparisonState.comparisonType || '',
    };
  }

  public serialize(contextId: string): string {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }
    return JSON.stringify(this.contexts.get(contextId));
  }

  public deserialize(serializedContext: string): Context {
    const context = JSON.parse(serializedContext);
    this.contexts.set(context.id, context);
    this.recordEvent('context.deserialized', context.id, { context });
    return this.cloneContext(context);
  }

  public validate(context: Context): boolean {
    return (
      !!context.id &&
      !!context.name &&
      !!context.type &&
      !!context.createdTime &&
      !!context.updatedTime &&
      !!context.owner &&
      !!context.workspace
    );
  }

  private updateContext(contextId: string, updates: Partial<Context>): Context {
    if (!this.contexts.has(contextId)) {
      throw new Error(`Context ${contextId} not found`);
    }

    const context = this.contexts.get(contextId)!;
    const updatedContext = { ...context, ...updates, updatedTime: new Date().toISOString() };
    this.contexts.set(contextId, updatedContext);
    return updatedContext;
  }

  private cloneContext(context: Context): Context {
    return JSON.parse(JSON.stringify(context));
  }

  private cloneWorkspace(workspace: Workspace): Workspace {
    return JSON.parse(JSON.stringify(workspace));
  }

  private generateId(): string {
    return `ctx_${Math.random().toString(36).substring(2, 15)}_${Date.now()}`;
  }

  private recordEvent(type: string, contextId: string, metadata: Record<string, unknown>): void {
    const event: ContextEvent = {
      id: this.generateId(),
      contextId,
      type,
      timestamp: new Date().toISOString(),
      metadata,
    };
    this.events.push(event);
  }

  private addContextToWorkspace(workspaceId: string, contextId: string): void {
    if (!this.workspaces.has(workspaceId)) {
      this.workspaces.set(workspaceId, {
        id: workspaceId,
        name: workspaceId,
        activeContexts: [],
        inactiveContexts: [],
        history: [],
        preferences: {},
      });
    }

    const workspace = this.workspaces.get(workspaceId)!;
    if (!workspace.activeContexts.includes(contextId)) {
      workspace.activeContexts.push(contextId);
    }
  }

  private removeContextFromWorkspace(workspaceId: string, contextId: string): void {
    if (!this.workspaces.has(workspaceId)) return;

    const workspace = this.workspaces.get(workspaceId)!;
    workspace.activeContexts = workspace.activeContexts.filter(id => id !== contextId);
    workspace.inactiveContexts = workspace.inactiveContexts.filter(id => id !== contextId);
  }
}