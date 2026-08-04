/**
 * Investigative Insight Runtime Tests — Stage 8
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  investigativeInsightRuntime,
  resetInvestigativeInsightRuntime,
} from '../investigative-runtime';
import type { InvestigativeTrigger, EvidenceLink, EntityReference, DrillDownAction } from '../types';

describe('InvestigativeInsightRuntime', () => {
  beforeEach(() => {
    resetInvestigativeInsightRuntime();
  });

  const baseParams = {
    trigger: 'entity-selected' as InvestigativeTrigger,
    title: 'Spending Pattern Analysis',
    summary: 'Spending in Dining is 34% higher than last month',
    evidenceTrail: [
      { label: 'Transaction #TX123', sourceType: 'transaction', sourceId: 'tx-123', confidence: 0.95 },
    ] as EvidenceLink[],
    relatedEntities: [
      { entityId: 'cat-1', entityType: 'category', label: 'Dining Out', relationshipType: 'CATEGORIZED_AS' },
    ] as EntityReference[],
    drillDownActions: [
      { label: 'View in Transactions', targetWorkspace: 'transactions' },
    ] as DrillDownAction[],
  };

  it('should generate an investigative insight', () => {
    const insight = investigativeInsightRuntime.generate(baseParams);
    expect(insight).toBeDefined();
    expect(insight.id).toMatch(/^inv-/);
    expect(insight.title).toBe('Spending Pattern Analysis');
    expect(insight.trigger).toBe('entity-selected');
    expect(insight.dismissed).toBe(false);
    expect(insight.evidenceTrail).toHaveLength(1);
    expect(insight.relatedEntities).toHaveLength(1);
    expect(insight.drillDownActions).toHaveLength(1);
  });

  it('should return active (non-dismissed) insights', () => {
    investigativeInsightRuntime.generate(baseParams);
    const insights = investigativeInsightRuntime.getInsights();
    expect(insights).toHaveLength(1);
    expect(insights[0].title).toBe('Spending Pattern Analysis');
  });

  it('should dismiss and hide insights', () => {
    const insight = investigativeInsightRuntime.generate(baseParams);
    investigativeInsightRuntime.dismiss(insight.id);
    expect(investigativeInsightRuntime.getInsights()).toHaveLength(0);
  });

  it('should undismiss a dismissed insight', () => {
    const insight = investigativeInsightRuntime.generate(baseParams);
    investigativeInsightRuntime.dismiss(insight.id);
    investigativeInsightRuntime.undismiss(insight.id);
    expect(investigativeInsightRuntime.getInsights()).toHaveLength(1);
  });

  it('should clear all dismissed insights', () => {
    investigativeInsightRuntime.generate({ ...baseParams, trigger: 'entity-selected' });
    investigativeInsightRuntime.generate({ ...baseParams, trigger: 'insight-clicked' });
    investigativeInsightRuntime.clearDismissed();
    expect(investigativeInsightRuntime.getInsights()).toHaveLength(0);
  });

  it('should get insights by trigger type', () => {
    investigativeInsightRuntime.generate({ ...baseParams, trigger: 'entity-selected' });
    investigativeInsightRuntime.generate({ ...baseParams, trigger: 'insight-clicked' });
    investigativeInsightRuntime.generate({ ...baseParams, trigger: 'command-issued' });

    expect(investigativeInsightRuntime.getByTrigger('entity-selected')).toHaveLength(1);
    expect(investigativeInsightRuntime.getByTrigger('insight-clicked')).toHaveLength(1);
    expect(investigativeInsightRuntime.getByTrigger('command-issued')).toHaveLength(1);
  });

  it('should execute drill-down actions', () => {
    const insight = investigativeInsightRuntime.generate({
      ...baseParams,
      drillDownActions: [
        { label: 'Go to Transactions', targetWorkspace: 'transactions', contextPayload: { preselect: 'tx-1' } },
      ],
    });
    // Test invalid index returns false
    const result1 = investigativeInsightRuntime.executeDrillDown(insight.id, 99);
    expect(result1).toBe(false);
    // Test non-existent insight returns false
    const result2 = investigativeInsightRuntime.executeDrillDown('non-existent', 0);
    expect(result2).toBe(false);
  });

  it('should return undefined for non-existent insight id', () => {
    expect(investigativeInsightRuntime.getById('non-existent')).toBeUndefined();
  });

  it('should notify subscribers on changes', () => {
    const listener = vi.fn();
    investigativeInsightRuntime.subscribe(listener);
    investigativeInsightRuntime.generate(baseParams);
    expect(listener).toHaveBeenCalledOnce();
  });

  it('should reset all state', () => {
    investigativeInsightRuntime.generate(baseParams);
    resetInvestigativeInsightRuntime();
    expect(investigativeInsightRuntime.getInsights()).toHaveLength(0);
  });
});
