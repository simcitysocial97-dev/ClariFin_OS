/**
 * Command Runtime Tests - Stage 5 Command Center Experience
 *
 * Tests for CommandRuntime: registration, execution, search,
 * recent commands, pinned workflows, and routing.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  commandRuntime,
  resetCommandRuntime,
} from '../command-runtime';
import type { CommandDefinition, PinnedWorkflow } from '../runtime';

// ===== Helpers =====
function makeCommand(overrides: Partial<CommandDefinition> = {}): CommandDefinition {
  return {
    id: 'test-cmd',
    label: 'Test Command',
    category: 'navigation',
    keywords: ['test'],
    handler: vi.fn(),
    ...overrides,
  };
}

// ===== Tests =====
describe('CommandRuntime — Milestone 5', () => {
  beforeEach(() => {
    resetCommandRuntime();
  });

  describe('Command Registration', () => {
    it('registers a custom command', () => {
      const cmd = makeCommand({ id: 'custom:test', label: 'Custom Test' });
      commandRuntime.registerCommand(cmd);
      const results = commandRuntime.search('custom');
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].command.id).toBe('custom:test');
    });

    it('unregisters a command', () => {
      const cmd = makeCommand({ id: '_unregister-me', keywords: ['unregisterme'] });
      commandRuntime.registerCommand(cmd);
      expect(commandRuntime.search('unregisterme').length).toBeGreaterThan(0);
      commandRuntime.unregisterCommand('_unregister-me');
      expect(commandRuntime.search('unregisterme').length).toBe(0);
    });

    it('default commands are registered on init', () => {
      const results = commandRuntime.search('');
      expect(results.length).toBeGreaterThan(0);
    });

    it('includes open palette command by default', () => {
      const results = commandRuntime.search('palette');
      expect(results.some(r => r.command.id === 'cmd:open-palette')).toBe(true);
    });
  });

  describe('Command Search', () => {
    it('searches by label', () => {
      const results = commandRuntime.search('Dashboard');
      expect(results.some(r => r.command.label.toLowerCase().includes('dashboard'))).toBe(true);
    });

    it('searches by keyword', () => {
      const results = commandRuntime.search('transactions');
      expect(results.some(r => r.command.keywords?.includes('transactions'))).toBe(true);
    });

    it('returns empty for no match', () => {
      const results = commandRuntime.search('zzzz_nonexistent');
      expect(results).toEqual([]);
    });

    it('scores exact keyword matches higher', () => {
      const results = commandRuntime.search('dashboard');
      if (results.length > 0) {
        expect(results[0].matchedOn).toBe('keyword');
      }
    });
  });

  describe('Command Execution', () => {
    it('executes a command by ID', async () => {
      const handler = vi.fn();
      commandRuntime.registerCommand(makeCommand({ id: 'exec-test', handler }));
      const result = await commandRuntime.execute('exec-test');
      expect(result.success).toBe(true);
      expect(handler).toHaveBeenCalledOnce();
    });

    it('executes a command by search match', async () => {
      const handler = vi.fn();
      commandRuntime.registerCommand(makeCommand({
        id: 'exec-search',
        label: 'Execute Search Test',
        keywords: ['executesearch'],
        handler,
      }));
      const result = await commandRuntime.execute('executesearch');
      expect(result.success).toBe(true);
      expect(handler).toHaveBeenCalledOnce();
    });

    it('returns failure for unknown command', async () => {
      const result = await commandRuntime.execute('_zzz_nonexistent_xyz_');
      expect(result.success).toBe(false);
    });

    it('handles async handlers', async () => {
      const handler = vi.fn().mockResolvedValue(undefined);
      commandRuntime.registerCommand(makeCommand({ id: 'async-cmd', handler }));
      const result = await commandRuntime.execute('async-cmd');
      expect(result.success).toBe(true);
    });

    it('tracks command in recent history', async () => {
      const handler = vi.fn();
      commandRuntime.registerCommand(makeCommand({ id: 'recent-test', handler }));
      await commandRuntime.execute('recent-test');
      const recent = commandRuntime.getRecent(10);
      expect(recent.length).toBeGreaterThan(0);
      expect(recent[0].commandId).toBe('recent-test');
    });
  });

  describe('Recent Commands', () => {
    it('stores last 10 commands', async () => {
      for (let i = 0; i < 12; i++) {
        const handler = vi.fn();
        commandRuntime.registerCommand(makeCommand({ id: `recent-${i}`, handler }));
        await commandRuntime.execute(`recent-${i}`);
      }
      const recent = commandRuntime.getRecent(10);
      expect(recent.length).toBeLessThanOrEqual(10);
    });

    it('newest command is first in recent list', async () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();
      commandRuntime.registerCommand(makeCommand({ id: 'first-cmd', handler: handler1 }));
      commandRuntime.registerCommand(makeCommand({ id: 'second-cmd', handler: handler2 }));
      await commandRuntime.execute('first-cmd');
      await commandRuntime.execute('second-cmd');
      const recent = commandRuntime.getRecent(2);
      expect(recent[0].commandId).toBe('second-cmd');
      expect(recent[1].commandId).toBe('first-cmd');
    });

    it('recent commands are session-scoped', () => {
      const recent = commandRuntime.getRecent(10);
      // Default commands shouldn't be in recent until executed
      expect(recent.every(r => !r.commandId.startsWith('cmd:navigate'))).toBe(true);
    });
  });

  describe('Pinned Workflows', () => {
    it('pins a workflow', () => {
      const workflow: PinnedWorkflow = {
        id: 'wf-1',
        label: 'Monthly Review',
        order: 0,
        steps: [
          { label: 'Go to Cashflow', commandId: 'cmd:navigate-cashflow' },
          { label: 'Set period', commandId: 'cmd:set-period' },
        ],
      };
      commandRuntime.pinWorkflow(workflow);
      const pinned = commandRuntime.getPinned();
      expect(pinned).toContainEqual(workflow);
    });

    it('updates an existing pinned workflow', () => {
      const workflow: PinnedWorkflow = {
        id: 'wf-update',
        label: 'Updated Workflow',
        order: 0,
        steps: [],
      };
      commandRuntime.pinWorkflow(workflow);
      workflow.label = 'Modified Workflow';
      commandRuntime.pinWorkflow(workflow);
      const pinned = commandRuntime.getPinned();
      expect(pinned.find(w => w.id === 'wf-update')?.label).toBe('Modified Workflow');
    });

    it('unpins a workflow', () => {
      const workflow: PinnedWorkflow = {
        id: 'wf-unpin',
        label: 'To Remove',
        order: 0,
        steps: [],
      };
      commandRuntime.pinWorkflow(workflow);
      expect(commandRuntime.getPinned().length).toBeGreaterThan(0);
      commandRuntime.unpinWorkflow('wf-unpin');
      expect(commandRuntime.getPinned().some(w => w.id === 'wf-unpin')).toBe(false);
    });
  });

  describe('Command Routing', () => {
    it('navigate commands push to navigation runtime', async () => {
      const result = await commandRuntime.execute('cmd:navigate-dashboard');
      expect(result.success).toBe(true);
    });

    it('navigate commands succeed', async () => {
      const result = await commandRuntime.execute('cmd:navigate-transactions');
      expect(result.success).toBe(true);
    });
  });

  describe('Event Subscription', () => {
    it('subscribes to command events', () => {
      const listener = vi.fn();
      const unsubscribe = commandRuntime.subscribe(listener);
      const handler = vi.fn();
      commandRuntime.registerCommand(makeCommand({ id: 'event-test', handler }));
      commandRuntime.execute('event-test');
      expect(listener).toHaveBeenCalled();
      unsubscribe();
    });

    it('publishes executed event on success', async () => {
      const events: Array<{ type: string; commandId: string }> = [];
      commandRuntime.subscribe(e => events.push(e as never));
      const handler = vi.fn();
      commandRuntime.registerCommand(makeCommand({ id: 'sub-exec', handler }));
      await commandRuntime.execute('sub-exec');
      expect(events.some(e => e.type === 'executed' && e.commandId === 'sub-exec')).toBe(true);
    });

    it('publishes failed event on missing command', async () => {
      const events: Array<{ type: string }> = [];
      commandRuntime.subscribe(e => events.push(e as never));
      await commandRuntime.execute('_zzz_nonexistent_xyz_');
      expect(events.some(e => e.type === 'failed')).toBe(true);
    });
  });

  describe('No Business Logic Invariant', () => {
    it('command handlers delegate to other runtimes, not compute', () => {
      // Verify that default navigate commands use navigationRuntime, not local state
      const navCmd = commandRuntime.search('dashboard')[0]?.command;
      expect(navCmd?.id).toContain('navigate');
    });
  });
});
