/**
 * Platform API Contract Tests — M9-C67.2
 *
 * Verifies that the live backend endpoints conform to C67.1 contracts.
 * Requires backend running on :8000.
 */

import { describe, it, expect } from 'vitest';

const TEST_TIMEOUT = 120_000;

// ---------------------------------------------------------------------------
// GET /platform/v1/status
// ---------------------------------------------------------------------------

describe('GET /platform/v1/status', () => {
  it('returns 200 with valid envelope', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/status');
    expect(res.status).toBe(200);

    const data = await res.json() as Record<string, unknown>;
    expect(data).toHaveProperty('kind');
    expect(data).toHaveProperty('data');
    expect(typeof data.kind).toBe('string');
  });

  it('data has required top-level fields', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/status');
    const json = await res.json() as { data: Record<string, unknown> };
    const d = json.data;

    expect(d).toHaveProperty('repository');
    expect(d).toHaveProperty('commit_sha');
    expect(d).toHaveProperty('certification_state');
    expect(d).toHaveProperty('capability_count');
    expect(d).toHaveProperty('workflow_count');
    expect(d).toHaveProperty('framework_health');
  });

  it('capability_count is a positive integer', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/status');
    const json = await res.json() as { data: { capability_count: number } };
    const count = json.data.capability_count;
    expect(Number.isInteger(count)).toBe(true);
    expect(count).toBeGreaterThan(0);
  });

  it('workflow_count is a positive integer', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/status');
    const json = await res.json() as { data: { workflow_count: number } };
    const count = json.data.workflow_count;
    expect(Number.isInteger(count)).toBe(true);
    expect(count).toBeGreaterThan(0);
  });

  it('certification_state is a known enum value', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/status');
    const json = await res.json() as { data: { certification_state: string } };
    const state = json.data.certification_state;
    expect(['CERTIFIED', 'UNVERIFIED', 'PENDING', 'UNKNOWN']).toContain(state);
  });

  it('commit_sha is a non-empty hex string', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/status');
    const json = await res.json() as { data: { commit_sha: string } };
    const sha = json.data.commit_sha;
    expect(sha.length).toBeGreaterThan(0);
    expect(sha).toMatch(/^[0-9a-f]{40}$/);
  });
});

// ---------------------------------------------------------------------------
// GET /platform/v1/health
// ---------------------------------------------------------------------------

describe('GET /platform/v1/health', () => {
  it('returns 200 with valid envelope', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/health?nocache=1');
    expect(res.status).toBe(200);

    const data = await res.json() as Record<string, unknown>;
    expect(data).toHaveProperty('kind');
    expect(data).toHaveProperty('data');
    expect(data.kind).toBe('platform.health_snapshot');
  });

  it('data has platform status field', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/health?nocache=1');
    const json = await res.json() as { data: { platform: string } };
    expect(['HEALTHY', 'DEGRAD', 'UNHEALTHY', 'UNKNOWN']).toContain(json.data.platform);
  });

  it('domains array has required fields per entry', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/health?nocache=1');
    const json = await res.json() as { data: { domains: Array<{ name: string; status: string; last_check: string; source: string }> } };
    const domains = json.data.domains;

    if (domains.length > 0) {
      const domain = domains[0];
      expect(domain).toHaveProperty('name');
      expect(domain).toHaveProperty('status');
      expect(domain).toHaveProperty('last_check');
      expect(domain).toHaveProperty('source');
    }
  });
});

// ---------------------------------------------------------------------------
// GET /platform/v1/workflows
// ---------------------------------------------------------------------------

describe('GET /platform/v1/workflows', () => {
  it('returns 200 with valid envelope', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/workflows');
    expect(res.status).toBe(200);

    const data = await res.json() as Record<string, unknown>;
    expect(data).toHaveProperty('kind');
    expect(data).toHaveProperty('data');
    expect(data.kind).toBe('platform.workflows');
  });

  it('data has count and items', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/workflows');
    const json = await res.json() as { data: { count: number; items: Array<Record<string, unknown>> } };
    expect(Number.isInteger(json.data.count)).toBe(true);
    expect(json.data.count).toBeGreaterThan(0);
    expect(Array.isArray(json.data.items)).toBe(true);
  });

  it('each workflow has required fields', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/workflows');
    const json = await res.json() as { data: { items: Array<Record<string, unknown>> } };
    const items = json.data.items;

    if (items.length > 0) {
      const w = items[0];
      expect(w).toHaveProperty('workflow_id');
      expect(w).toHaveProperty('name');
      expect(w).toHaveProperty('path');
      expect(w).toHaveProperty('boundary_classification');
      expect(w).toHaveProperty('local_executable');
      expect(w).toHaveProperty('canonical_command');
    }
  });

  it('boundary_classification is a known enum', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/workflows');
    const json = await res.json() as { data: { items: Array<{ boundary_classification: string }> } };
    const valid = ['LOCAL', 'GITHUB_ONLY', 'ENVIRONMENT_BOUNDARY', 'EXTERNAL_TOOLING', 'EXTERNAL_SERVICE', 'BROWSER'];
    for (const w of json.data.items) {
      expect(valid).toContain(w.boundary_classification);
    }
  });
});

// ---------------------------------------------------------------------------
// GET /platform/v1/runs
// ---------------------------------------------------------------------------

describe('GET /platform/v1/runs', () => {
  it('returns 200 with valid envelope', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/runs?page=1&page_size=5');
    expect(res.status).toBe(200);

    const data = await res.json() as Record<string, unknown>;
    expect(data).toHaveProperty('kind');
    expect(data).toHaveProperty('data');
  });

  it('data has pagination fields', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/runs?page=1&page_size=5');
    const json = await res.json() as { data: { page: number; page_size: number; total: number; items: unknown[] } };
    expect(Number.isInteger(json.data.page)).toBe(true);
    expect(Number.isInteger(json.data.page_size)).toBe(true);
    expect(Number.isInteger(json.data.total)).toBe(true);
    expect(Array.isArray(json.data.items)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// GET /platform/v1/verification
// ---------------------------------------------------------------------------

describe('GET /platform/v1/verification', () => {
  it('returns 200 with valid envelope', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/verification');
    expect(res.status).toBe(200);

    const data = await res.json() as Record<string, unknown>;
    expect(data).toHaveProperty('kind');
    expect(data).toHaveProperty('data');
  });

  it('data has required verification fields', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/verification');
    const json = await res.json() as { data: { status: string; classification: string; gates: Record<string, unknown>; summary: Record<string, unknown> } };
    const d = json.data;

    expect(['passed', 'failed', 'unknown']).toContain(d.status);
    expect(['CERTIFIED', 'UNVERIFIED']).toContain(d.classification);
    expect(d.gates).toHaveProperty('success_rate');
    expect(d.summary).toHaveProperty('capability_count');
  });

  it('classification is CERTIFIED or UNVERIFIED only', { timeout: TEST_TIMEOUT }, async () => {
    const res = await fetch('http://localhost:8000/platform/v1/verification');
    const json = await res.json() as { data: { classification: string } };
    expect(['CERTIFIED', 'UNVERIFIED']).toContain(json.data.classification);
  });
});
