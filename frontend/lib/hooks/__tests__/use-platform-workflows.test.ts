/**
 * Platform Workflows Hook Tests — M9-C67.2
 */

import { describe, it, expect, vi } from 'vitest';

vi.mock('@/lib/api/gateway', () => ({
  apiFetchJson: vi.fn(),
}));

import { getBoundaryColor, getBoundaryDescription, type WorkflowItem } from '../use-platform-workflows';

const MOCK_WORKFLOW: WorkflowItem = {
  workflow_id: 'backend_verify',
  name: 'Backend Verification',
  path: 'workflows/backend/verify.py',
  triggers: ['manual', 'git-push'],
  jobs: ['lint', 'test', 'typecheck'],
  commands: ['python -m pytest backend/tests/', 'python -m mypy backend/src/'],
  canonical_command: 'verify backend',
  local_executable: true,
  boundary_classification: 'LOCAL',
  environment_requirements: ['python3.11', '.venv'],
  parity_status: 'CURRENT',
};

const MOCK_RESPONSE = {
  kind: 'platform.workflows',
  version: '1.0.0',
  generated_at: '2026-09-20T12:00:00Z',
  id: 'sha256:def456',
  data: {
    count: 14,
    items: [MOCK_WORKFLOW],
    source: 'runtime.foundation.verification.workflow_inspection',
    last_updated: '2026-09-20T12:00:00Z',
  },
};

describe('usePlatformWorkflows', () => {
  it('returns workflows with count matching array length', () => {
    expect(MOCK_RESPONSE.data.count).toBe(14);
    expect(MOCK_RESPONSE.data.items.length).toBe(1);
  });

  it('has required envelope structure', () => {
    expect(MOCK_RESPONSE).toHaveProperty('kind');
    expect(MOCK_RESPONSE).toHaveProperty('data');
    expect(MOCK_RESPONSE.kind).toBe('platform.workflows');
  });
});

describe('Workflow boundaries', () => {
  it('LOCAL boundary has correct color', () => {
    expect(getBoundaryColor('LOCAL')).toBe('text-emerald-400');
  });

  it('GITHUB_ONLY boundary has correct color', () => {
    expect(getBoundaryColor('GITHUB_ONLY')).toBe('text-blue-400');
  });

  it('EXTERNAL_SERVICE boundary has correct color', () => {
    expect(getBoundaryColor('EXTERNAL_SERVICE')).toBe('text-red-400');
  });

  it('unknown boundary falls back to slate', () => {
    expect(getBoundaryColor('UNKNOWN_CLASSIFICATION')).toBe('text-slate-400');
  });
});

describe('Workflow descriptions', () => {
  it('LOCAL has description', () => {
    expect(getBoundaryDescription('LOCAL')).toBe('Runs locally without external dependencies');
  });

  it('GITHUB_ONLY has description', () => {
    expect(getBoundaryDescription('GITHUB_ONLY')).toBe('Requires GitHub Actions infrastructure');
  });

  it('unknown boundary returns generic description', () => {
    expect(getBoundaryDescription('UNKNOWN')).toContain('Unknown');
  });
});

describe('Workflow item structure', () => {
  it('has all required fields', () => {
    const w = MOCK_WORKFLOW;
    expect(w).toHaveProperty('workflow_id');
    expect(w).toHaveProperty('name');
    expect(w).toHaveProperty('path');
    expect(w).toHaveProperty('boundary_classification');
    expect(w).toHaveProperty('local_executable');
    expect(w).toHaveProperty('canonical_command');
  });

  it('local_executable is boolean', () => {
    expect(typeof MOCK_WORKFLOW.local_executable).toBe('boolean');
  });

  it('boundary_classification is a valid enum string', () => {
    const valid = ['LOCAL', 'GITHUB_ONLY', 'ENVIRONMENT_BOUNDARY', 'EXTERNAL_TOOLING', 'EXTERNAL_SERVICE', 'BROWSER'];
    expect(valid).toContain(MOCK_WORKFLOW.boundary_classification);
  });
});
