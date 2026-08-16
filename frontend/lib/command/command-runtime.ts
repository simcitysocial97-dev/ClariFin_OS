/**
 * Command Runtime Implementation — Stage 5 Financial Operating System
 *
 * Full implementation of the Command Runtime per
 * FINANCIAL_OS_SHELL_ARCHITECTURE.md §6.
 *
 * Architecture: Command Runtime → NavigationRuntime / WorkspaceRuntime / etc.
 */

import type {
  CommandDefinition,
  CommandResult,
  CommandSearchResult,
  CommandHistoryEntry,
  PinnedWorkflow,
  CommandEvent,
  CommandRuntime,
} from './runtime';
import { navigationRuntime } from '../runtime/navigation-runtime';

// ─── State ──────────────────────────────────────────────────────────────────

const _commands: Map<string, CommandDefinition> = new Map();
const _recentCommands: CommandHistoryEntry[] = [];
const _pinnedWorkflows: PinnedWorkflow[] = [];
const _listeners: Set<(event: CommandEvent) => void> = new Set();

// ─── Default Commands ────────────────────────────────────────────────────────

function createDefaultCommands(): CommandDefinition[] {
  return [
    {
      id: 'cmd:open-palette',
      label: 'Open Command Palette',
      category: 'navigation',
      keywords: ['command', 'palette', 'search', 'run', 'execute'],
      shortcut: 'mod+k',
      handler: () => {
        const event = new CustomEvent('os-open-command-palette');
        window.dispatchEvent(event);
      },
    },
    {
      id: 'cmd:clear-selection',
      label: 'Clear Selection',
      category: 'navigation',
      keywords: ['clear', 'selection', 'deselect', 'reset'],
      shortcut: 'escape',
      handler: () => {
        const event = new CustomEvent('os-clear-selection');
        window.dispatchEvent(event);
      },
    },
    {
      id: 'cmd:shortcut-help',
      label: 'Show Keyboard Shortcuts',
      category: 'navigation',
      keywords: ['help', 'shortcuts', 'key', 'keys', 'guide'],
      shortcut: '?',
      handler: () => {
        const event = new CustomEvent('os-show-shortcuts');
        window.dispatchEvent(event);
      },
    },
    {
      id: 'cmd:navigate-dashboard',
      label: 'Go to Dashboard',
      category: 'navigation',
      keywords: ['dashboard', 'home', 'main', 'overview'],
      shortcut: 'mod+1',
      handler: () => {
        navigationRuntime.pushPath('/dashboard');
      },
      workspaceId: 'dashboard',
    },
    {
      id: 'cmd:navigate-transactions',
      label: 'Go to Transactions',
      category: 'navigation',
      keywords: ['transactions', 'tx', 'payment', 'spending', 'money out'],
      shortcut: 'mod+2',
      handler: () => {
        navigationRuntime.pushPath('/transactions');
      },
      workspaceId: 'transactions',
    },
    {
      id: 'cmd:navigate-accounts',
      label: 'Go to Accounts',
      category: 'navigation',
      keywords: ['accounts', 'bank', 'account', 'balance'],
      shortcut: 'mod+3',
      handler: () => {
        navigationRuntime.pushPath('/accounts');
      },
      workspaceId: 'accounts',
    },
    {
      id: 'cmd:navigate-net-worth',
      label: 'Go to Net Worth',
      category: 'navigation',
      keywords: ['net worth', 'assets', 'wealth', 'portfolio'],
      shortcut: 'mod+4',
      handler: () => {
        navigationRuntime.pushPath('/net-worth');
      },
      workspaceId: 'net-worth',
    },
    {
      id: 'cmd:navigate-cashflow',
      label: 'Go to Cash Flow',
      category: 'navigation',
      keywords: ['cash flow', 'cashflow', 'income', 'expense', 'flow'],
      shortcut: 'mod+5',
      handler: () => {
        navigationRuntime.pushPath('/cashflow');
      },
      workspaceId: 'cashflow',
    },
    {
      id: 'cmd:navigate-investments',
      label: 'Go to Investments',
      category: 'navigation',
      keywords: ['investments', 'stocks', 'funds', 'portfolio'],
      shortcut: 'mod+6',
      handler: () => {
        navigationRuntime.pushPath('/investments');
      },
      workspaceId: 'investments',
    },
    {
      id: 'cmd:navigate-loans',
      label: 'Go to Loans',
      category: 'navigation',
      keywords: ['loans', 'mortgage', 'debt', 'credit'],
      shortcut: 'mod+7',
      handler: () => {
        navigationRuntime.pushPath('/loans');
      },
      workspaceId: 'loans',
    },
    {
      id: 'cmd:navigate-behaviour',
      label: 'Go to Behaviour',
      category: 'navigation',
      keywords: ['behaviour', 'behavior', 'score', 'analysis'],
      shortcut: 'mod+8',
      handler: () => {
        navigationRuntime.pushPath('/behaviour');
      },
      workspaceId: 'behaviour',
    },
    {
      id: 'cmd:navigate-forecast',
      label: 'Go to Forecast',
      category: 'navigation',
      keywords: ['forecast', 'predict', 'projection', 'future'],
      shortcut: 'mod+9',
      handler: () => {
        navigationRuntime.pushPath('/forecast');
      },
      workspaceId: 'forecast',
    },
    // ── Graph commands (Stage 7) ───────────────────────────────────────
    {
      id: 'cmd:graph-explore',
      label: 'Explore Relationships (Graph)',
      category: 'graph',
      keywords: ['graph', 'relationships', 'explore', 'connections', 'network'],
      shortcut: 'mod+g',
      handler: () => {
        const event = new CustomEvent('os-graph-explore');
        window.dispatchEvent(event);
      },
    },
    {
      id: 'cmd:graph-close',
      label: 'Close Graph',
      category: 'graph',
      keywords: ['close graph', 'hide graph', 'exit graph'],
      handler: () => {
        const event = new CustomEvent('os-graph-close');
        window.dispatchEvent(event);
      },
    },
    // ── Intelligence commands (Stage 8) ───────────────────────────────────────
    {
      id: 'cmd:intelligence-investigate',
      label: 'Investigate Entity',
      category: 'intelligence',
      keywords: ['investigate', 'explore entity', 'drill down', 'insight', 'analyze'],
      shortcut: 'mod+i',
      handler: () => {
        const event = new CustomEvent('os-intelligence-investigate');
        window.dispatchEvent(event);
      },
    },
    {
      id: 'cmd:intelligence-clear',
      label: 'Clear Intelligence',
      category: 'intelligence',
      keywords: ['clear insights', 'reset intelligence', 'dismiss all insights'],
      handler: () => {
        const event = new CustomEvent('os-intelligence-clear');
        window.dispatchEvent(event);
      },
    },
  ];
}

// ─── NL Tokenizer ────────────────────────────────────────────────────────────

function tokenize(input: string): string[] {
  return input
    .toLowerCase()
    .replace(/[^\w\s\-]/g, ' ')
    .split(/\s+/)
    .filter(t => t.length > 0);
}

// ─── Score Calculation ───────────────────────────────────────────────────────

function scoreCommand(
  command: CommandDefinition,
  tokens: string[],
): { score: number; matchedOn: 'label' | 'keyword' | 'natural-language' } | null {
  if (tokens.length === 0) {
    return { score: 100, matchedOn: 'label' };
  }

  const labelLower = command.label.toLowerCase();
  const keywordsLower = command.keywords.map(k => k.toLowerCase());

  let score = 0;
  let matchedOn: 'label' | 'keyword' | 'natural-language' = 'keyword';

  // Exact keyword match (highest priority)
  for (const token of tokens) {
    if (keywordsLower.includes(token)) {
      score += 50;
      matchedOn = 'keyword';
    }
  }

  // Label substring match
  for (const token of tokens) {
    if (labelLower.includes(token)) {
      score += 40;
      if (matchedOn !== 'keyword') matchedOn = 'label';
    }
  }

  // Natural language partial match
  if (score === 0) {
    for (const token of tokens) {
      const anyKeywordMatch = keywordsLower.some(k => k.includes(token) || token.includes(k));
      if (anyKeywordMatch || labelLower.includes(token)) {
        score += 10;
        matchedOn = 'natural-language';
      }
    }
  }

  return score > 0 ? { score, matchedOn } : null;
}

// ─── Execute ─────────────────────────────────────────────────────────────────

async function executeCommand(
  command: CommandDefinition,
): Promise<CommandResult> {
  try {
    await command.handler();
    return {
      success: true,
      type: 'info',
      commandId: command.id,
      message: `Executed: ${command.label}`,
    };
  } catch (err) {
    return {
      success: false,
      type: 'info',
      commandId: command.id,
      message: err instanceof Error ? err.message : 'Command failed',
    };
  }
}

// ─── Public API ──────────────────────────────────────────────────────────────

function registerCommand(command: CommandDefinition): void {
  _commands.set(command.id, command);
  const event: CommandEvent = {
    type: 'executed',
    commandId: command.id,
    input: `registered:${command.label}`,
    timestamp: Date.now(),
  };
  _listeners.forEach(fn => fn(event));
}

function unregisterCommand(commandId: string): boolean {
  return _commands.delete(commandId);
}

async function execute(input: string): Promise<CommandResult> {
  let command: CommandDefinition | undefined;
  const inputStr = input;

  if (_commands.has(inputStr)) {
    command = _commands.get(inputStr);
  } else {
    // Search for best match
    const results = search(inputStr);
    if (results.length > 0) {
      command = results[0].command;
    }
  }

  if (!command) {
    const event: CommandEvent = {
      type: 'failed',
      commandId: '_unknown_',
      input: inputStr,
      timestamp: Date.now(),
    };
    _listeners.forEach(fn => fn(event));
    return { success: false, type: 'info', message: `No command found for: "${inputStr}"` };
  }

  const result = await executeCommand(command);

  // Add to recent commands
  _recentCommands.unshift({
    commandId: command.id,
    input: inputStr,
    timestamp: Date.now(),
    result,
  });
  if (_recentCommands.length > 10) _recentCommands.pop();

  // Publish event
  const event: CommandEvent = {
    type: result.success ? 'executed' : 'failed',
    commandId: command.id,
    input: inputStr,
    timestamp: Date.now(),
  };
  _listeners.forEach(fn => fn(event));

  return result;
}

function search(query: string): CommandSearchResult[] {
  const tokens = tokenize(query);
  const results: CommandSearchResult[] = [];

  for (const command of _commands.values()) {
    const scored = scoreCommand(command, tokens);
    if (scored) {
      results.push({ command, score: scored.score, matchedOn: scored.matchedOn });
    }
  }

  return results.sort((a, b) => b.score - a.score);
}

function getRecent(limit = 10): CommandHistoryEntry[] {
  return _recentCommands.slice(0, limit);
}

function getPinned(): PinnedWorkflow[] {
  return [..._pinnedWorkflows];
}

function pinWorkflow(workflow: PinnedWorkflow): void {
  const existing = _pinnedWorkflows.findIndex(w => w.id === workflow.id);
  if (existing >= 0) {
    _pinnedWorkflows[existing] = workflow;
  } else {
    _pinnedWorkflows.push(workflow);
  }
  // Persist to localStorage
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem('command-pinned-workflows', JSON.stringify(_pinnedWorkflows));
    } catch { /* ignore */ }
  }
}

function unpinWorkflow(workflowId: string): boolean {
  const idx = _pinnedWorkflows.findIndex(w => w.id === workflowId);
  if (idx >= 0) {
    _pinnedWorkflows.splice(idx, 1);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('command-pinned-workflows', JSON.stringify(_pinnedWorkflows));
      } catch { /* ignore */ }
    }
    return true;
  }
  return false;
}

function subscribe(listener: (event: CommandEvent) => void): () => void {
  _listeners.add(listener);
  return () => {
    _listeners.delete(listener);
  };
}

// ─── Init ────────────────────────────────────────────────────────────────────

function init(): void {
  // Register default commands
  for (const cmd of createDefaultCommands()) {
    _commands.set(cmd.id, cmd);
  }

  // Restore pinned workflows from localStorage
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem('command-pinned-workflows');
      if (stored) {
        const parsed = JSON.parse(stored) as PinnedWorkflow[];
        _pinnedWorkflows.push(...parsed);
      }
    } catch { /* ignore */ }
  }
}

init();

// ─── Singleton Export ────────────────────────────────────────────────────────

export const commandRuntime: CommandRuntime = {
  registerCommand,
  unregisterCommand,
  execute,
  search,
  getRecent,
  getPinned,
  pinWorkflow,
  unpinWorkflow,
  subscribe,
};

export function resetCommandRuntime(): void {
  _commands.clear();
  _recentCommands.length = 0;
  _pinnedWorkflows.length = 0;
  _listeners.clear();
  init();
}
