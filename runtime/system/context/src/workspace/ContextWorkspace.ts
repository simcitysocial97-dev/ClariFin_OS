import { ContextRuntime } from './workspace/ContextRuntime';
import { Workspace } from '../models/types';


export class ContextWorkspace {
  private runtime: ContextRuntime;

  constructor() {
    this.runtime = ContextRuntime.getInstance();
  }

  public createWorkspace(workspaceId: string, name: string): Workspace {
    if (this.runtime['workspaces'].has(workspaceId)) {
      throw new Error(`Workspace ${workspaceId} already exists`);
    }

    const workspace: Workspace = {
      id: workspaceId,
      name,
      activeContexts: [],
      inactiveContexts: [],
      history: [],
      preferences: {},
    };

    this.runtime['workspaces'].set(workspaceId, workspace);
    this.runtime['recordEvent']('workspace.created', workspaceId, { workspace });
    return this.runtime['cloneWorkspace'](workspace);
  }

  public destroyWorkspace(workspaceId: string): void {
    if (!this.runtime['workspaces'].has(workspaceId)) {
      throw new Error(`Workspace ${workspaceId} not found`);
    }

    const workspace = this.runtime['workspaces'].get(workspaceId)!;
    this.runtime['recordEvent']('workspace.destroyed', workspaceId, { workspace });
    this.runtime['workspaces'].delete(workspaceId);
  }

  public getWorkspace(workspaceId: string): Workspace {
    return this.runtime.workspace(workspaceId);
  }

  public listWorkspaces(): Workspace[] {
    return Array.from(this.runtime['workspaces'].values()).map(ws =>
      this.runtime['cloneWorkspace'](ws)
    );
  }

  public addContextToWorkspace(workspaceId: string, contextId: string): void {
    this.runtime['addContextToWorkspace'](workspaceId, contextId);
  }

  public removeContextFromWorkspace(workspaceId: string, contextId: string): void {
    this.runtime['removeContextFromWorkspace'](workspaceId, contextId);
  }
}