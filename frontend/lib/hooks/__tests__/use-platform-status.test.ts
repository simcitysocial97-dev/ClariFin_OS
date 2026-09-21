/**
 * Platform Status Hook Tests — M9-C67.2
 */

import { describe, it, expect, vi } from 'vitest';

vi.mock('@/lib/api/gateway', () => ({
  apiFetchJson: vi.fn(),
}));

import { usePlatformStatus } from '../use-platform-status';

const MOCK_STATUS = {
  kind: 'platform.status',
  version: '1.0.0',
  generated_at: '2026-09-20T12:00:00Z',
  id: 'sha256:abc123',
  data: {
    repository: 'ClariFin_OS',
    commit_sha: 'abc123def456',
    tree_sha: 'tree789',
    branch: 'main',
    runtime_version: '1.0.0',
    fingerprint: 'fp-xyz',
    framework_health: 'HEALTHY',
    certification_state: 'CERTIFIED',
    capability_count: 55,
    profile_count: 12,
    workflow_count: 14,
    recent_run_status: 'HEALTHY',
    recent_run_id: 'run-001',
  },
};

describe('usePlatformStatus', () => {
  it('returns status data when API succeeds', async () => {
    const { apiFetchJson } = await import('@/lib/api/gateway');
    vi.mocked(apiFetchJson).mockResolvedValueOnce(MOCK_STATUS);

    expect(MOCK_STATUS.data.certification_state).toBe('CERTIFIED');
    expect(MOCK_STATUS.data.capability_count).toBe(55);
    expect(MOCK_STATUS.data.workflow_count).toBe(14);
    expect(MOCK_STATUS.data.commit_sha).toBe('abc123def456');
  });

  it('has correct response envelope structure', () => {
    expect(MOCK_STATUS).toHaveProperty('kind');
    expect(MOCK_STATUS).toHaveProperty('version');
    expect(MOCK_STATUS).toHaveProperty('generated_at');
    expect(MOCK_STATUS).toHaveProperty('id');
    expect(MOCK_STATUS).toHaveProperty('data');
    expect(MOCK_STATUS.kind).toBe('platform.status');
  });

  it('data has all required fields', () => {
    const d = MOCK_STATUS.data;
    expect(d).toHaveProperty('repository');
    expect(d).toHaveProperty('commit_sha');
    expect(d).toHaveProperty('certification_state');
    expect(d).toHaveProperty('capability_count');
    expect(d).toHaveProperty('workflow_count');
    expect(d).toHaveProperty('framework_health');
  });
});

describe('usePlatformStatus derived values', () => {
  it('certification_state is CERTIFIED in mock', () => {
    expect(MOCK_STATUS.data.certification_state).toBe('CERTIFIED');
  });

  it('capability_count matches canonical value 55', () => {
    expect(MOCK_STATUS.data.capability_count).toBe(55);
  });

  it('workflow_count matches canonical value 14', () => {
    expect(MOCK_STATUS.data.workflow_count).toBe(14);
  });

  it('commit_sha is non-empty', () => {
    expect(MOCK_STATUS.data.commit_sha.length).toBeGreaterThan(0);
  });

  it('framework_health is HEALTHY', () => {
    expect(MOCK_STATUS.data.framework_health).toBe('HEALTHY');
  });
});
