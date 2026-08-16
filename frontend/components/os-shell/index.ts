/**
 * OS Shell - Stage 8B Navigation Experience
 *
 * Permanent application shell that every workspace lives inside.
 * No business logic. No financial calculations. No API changes.
 *
 * Architecture: OS Shell → Workspace Registry → Runtimes (0-7.5)
 */

// Main shell components
export { AppShell } from './app-shell';
export { ShellProvider } from './shell-provider';

// Layout components
export { LeftRail } from './left-rail';
export { TopCommandBar } from './top-command-bar';
export { WorkspaceContainer } from './workspace-container';
export { WorkspaceOutlet } from './workspace-outlet';
export { RightInspector } from './right-inspector';
export { BottomTimeline } from './bottom-timeline';
export { BottomStatusBar } from './bottom-status-bar';
export { ResizableLayout } from './resizable-layout';

// Navigation experience components
export { DeepLinkSync } from './deep-link-sync';
export { WorkspaceHost, useWorkspaceHost } from './workspace-host';

// Context Panel (Milestone 4)
export { ContextPanel, useContextPanel } from './context-panel';

// Re-export runtime types for convenience
export type { WorkspaceName, WorkspaceState, WorkspaceContextValue } from '@/lib/workspace';
export type { GraphSelection, GraphNode, ExplainabilityPayload } from '@/lib/graph';
export type { SyncState, CacheStats } from '@/lib/performance';