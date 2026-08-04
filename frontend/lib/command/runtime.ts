/**
 * Command Runtime — Stage 5 Financial Operating System
 *
 * The Command Runtime is the control plane of the Financial OS.
 * It provides a unified interface for natural language commands,
 * keyboard shortcuts, quick actions, recent commands, pinned workflows,
 * and workspace launching.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §6
 */

import type { WorkspaceName } from '../workspace/workspace-context';

// ─── Command Definitions ─────────────────────────────────────────────────────

export type CommandCategory =
  | 'navigation'
  | 'action'
  | 'workflow'
  | 'intelligence'
  | 'graph';

export interface CommandDefinition {
  id: string;
  label: string;
  category: CommandCategory;
  keywords: string[];
  shortcut?: string; // e.g., "mod+k", "mod+1"
  workspaceId?: string;
  handler: () => void | Promise<void>;
  requiresContext?: boolean;
  icon?: string;
}

// ─── Execution Result ────────────────────────────────────────────────────────

export type CommandResultType =
  | 'navigation'
  | 'workspace-action'
  | 'insight'
  | 'overlay'
  | 'info';

export interface CommandResult {
  success: boolean;
  message?: string;
  commandId?: string;
  type: CommandResultType;
  targetWorkspace?: WorkspaceName;
  targetRoute?: string;
  payload?: Record<string, unknown>;
}

// ─── Search ──────────────────────────────────────────────────────────────────

export interface CommandSearchResult {
  command: CommandDefinition;
  score: number;
  matchedOn: 'label' | 'keyword' | 'natural-language';
}

// ─── History ─────────────────────────────────────────────────────────────────

export interface CommandHistoryEntry {
  commandId: string;
  input: string;
  timestamp: number;
  result: CommandResult;
}

// ─── Workflow ────────────────────────────────────────────────────────────────

export interface WorkflowStep {
  label: string;
  commandId: string;
  contextPayload?: Record<string, unknown>;
}

export interface PinnedWorkflow {
  id: string;
  label: string;
  steps: WorkflowStep[];
  icon?: string;
  order: number;
}

// ─── Event ───────────────────────────────────────────────────────────────────

export interface CommandEvent {
  type: 'executed' | 'failed' | 'cancelled';
  commandId: string;
  input: string;
  timestamp: number;
}

// ─── Context Runtime Import ──────────────────────────────────────────────────
// Lazy import to avoid circular dependency

// ─── Command Runtime Interface ──────────────────────────────────────────────

/**
 * The Command Runtime manages command registration,
 * execution, routing, and history.
 */
export interface CommandRuntime {
  registerCommand(command: CommandDefinition): void;
  unregisterCommand(commandId: string): boolean;
  execute(input: string | CommandDefinition['id']): Promise<CommandResult>;
  search(query: string): CommandSearchResult[];
  getRecent(limit: number): CommandHistoryEntry[];
  getPinned(): PinnedWorkflow[];
  pinWorkflow(workflow: PinnedWorkflow): void;
  unpinWorkflow(workflowId: string): boolean;
  subscribe(listener: (event: CommandEvent) => void): () => void;
}
