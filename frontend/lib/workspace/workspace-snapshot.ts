/**
 * Workspace State Snapshot — capture and restore ephemeral workspace state.
 *
 * Snapshot captures: scroll position, filters, sort config, selection IDs.
 * Stored per-workspace keyed by workspace name.
 * Restored on cold-mount when navigating back.
 */

// ===== Snapshot types =====
export interface WorkspaceStateSnapshot {
  workspaceId: string;
  scrollPosition: { x: number; y: number };
  filters: Record<string, unknown>;
  sortConfig: { field: string; direction: 'asc' | 'desc' } | null;
  selectionIds: string[];
  timestamp: number;
}

// ===== Snapshot store =====
const _snapshots = new Map<string, WorkspaceStateSnapshot>();

export function captureSnapshot(snapshot: WorkspaceStateSnapshot): void {
  _snapshots.set(snapshot.workspaceId, snapshot);
}

export function getSnapshot(workspaceId: string): WorkspaceStateSnapshot | null {
  return _snapshots.get(workspaceId) ?? null;
}

export function removeSnapshot(workspaceId: string): void {
  _snapshots.delete(workspaceId);
}

export function clearAllSnapshots(): void {
  _snapshots.clear();
}

export function getAllSnapshotKeys(): string[] {
  return Array.from(_snapshots.keys());
}
