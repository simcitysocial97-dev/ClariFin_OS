/**
 * Workspace Module - Stage 7.5 Runtime Consolidation
 *
 * Central export for workspace context and registry.
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
