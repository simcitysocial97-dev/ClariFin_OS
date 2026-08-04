/**
 * Workspace Module - Stage 8B Navigation Experience
 *
 * Central export for workspace context, registry, and lifecycle management.
 */

export {
  useWorkspaceContext,
  useWorkspace,
  WorkspaceContext,
  type WorkspaceName,
  type WorkspaceState,
  type WorkspaceContextValue,
} from './workspace-context';

export {
  WorkspaceRegistry,
  workspaceRegistry,
  type WorkspaceRegistration,
} from './workspace-registry';

export { WorkspaceProvider } from './workspace-provider';

// Workspace Lifecycle
export {
  WorkspaceLifecycleManager,
  workspaceLifecycleManager,
  useWorkspaceLifecycle,
  type MountState,
  type WorkspaceMountRecord,
  type TransitionState,
} from './workspace-lifecycle';

export {
  captureSnapshot,
  getSnapshot,
  removeSnapshot,
  clearAllSnapshots,
  getAllSnapshotKeys,
  type WorkspaceStateSnapshot,
} from './workspace-snapshot';

export { LRUCache, type LRUEntry } from './lru-cache';

