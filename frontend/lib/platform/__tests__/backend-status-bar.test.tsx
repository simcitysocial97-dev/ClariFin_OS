/**
 * M11 — the persistent backend status strip
 * =========================================
 *
 * The strip is the console's answer to "is the backend up?" on EVERY route,
 * including routes whose data has not started loading. That is what makes the
 * console useful while the backend is still warming — the per-page terminal
 * state only helps once a page's own read has resolved.
 *
 * Two properties are load-bearing and are what these tests pin:
 *
 *  1. The strip is driven ONLY by the liveness probe. It must not issue a
 *     `/platform/v1/*` read, because the cheapest platform read is 13.8 s cold
 *     and the whole point is an indicator that is never blocked by one.
 *  2. It stops re-probing once the backend is ready. A ready indicator that
 *     polls forever is a quieter version of the same defect.
 */

import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { PlatformBackendStatus } from '@/components/platform/backend-status-bar';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

/**
 * Stub the global fetch with a queue of liveness outcomes, recording every URL
 * the component asked for.
 */
function stubLiveness(outcomes: Array<'ok' | 'refused' | 'timeout'>) {
  const requested: string[] = [];
  let i = 0;
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    requested.push(String(url));
    const mode = outcomes[Math.min(i, outcomes.length - 1)];
    i += 1;
    if (mode === 'ok') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({ status: 'healthy' }),
        text: async () => '{}',
      });
    }
    if (mode === 'refused') {
      return Promise.reject(new TypeError('Failed to fetch'));
    }
    return new Promise((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => {
        const err = new Error('The operation was aborted.');
        err.name = 'AbortError';
        reject(err);
      });
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return { fetchMock, requested };
}

async function settle(ms = 0) {
  // Let the probe promise chain and the React state update flush.
  await new Promise((r) => setTimeout(r, ms));
  await new Promise((r) => setTimeout(r, 0));
}

describe('platform backend status strip (M11)', () => {
  it('shows BACKEND READY and confirms the timestamp once /health answers', async () => {
    stubLiveness(['ok']);
    render(<PlatformBackendStatus />);
    await settle();

    const strip = screen.getByTestId('platform-backend-status');
    expect(strip.getAttribute('data-backend-status')).toBe('ready');
    expect(screen.getByTestId('platform-backend-status-value').textContent).toContain(
      'BACKEND READY',
    );
    // A ready backend gets no re-check button: there is nothing to re-check.
    expect(screen.queryByTestId('platform-backend-status-retry')).toBeNull();
  });

  it('shows BACKEND STARTING when the connection is accepted but silent', async () => {
    stubLiveness(['timeout']);
    render(<PlatformBackendStatus livenessTimeoutMs={30} />);
    // Real wall clock: the `starting` verdict is produced by the deadline
    // actually elapsing, which is precisely the evidence the state rests on.
    await settle(80);

    const strip = screen.getByTestId('platform-backend-status');
    expect(strip.getAttribute('data-backend-status')).toBe('starting');
    const reason = screen.getByTestId('platform-backend-status-reason');
    expect(reason.textContent).toMatch(/still starting up/i);
    // A re-check affordance is right here; an error badge would send the
    // operator to restart a process that is mid-import.
    expect(screen.getByTestId('platform-backend-status-retry')).toBeTruthy();
  });

  it('shows BACKEND UNAVAILABLE when nothing is listening', async () => {
    stubLiveness(['refused']);
    render(<PlatformBackendStatus />);
    await settle();

    expect(
      screen.getByTestId('platform-backend-status').getAttribute('data-backend-status'),
    ).toBe('unavailable');
    const reason = screen.getByTestId('platform-backend-status-reason');
    expect(reason.textContent).toMatch(/not running/i);
    expect(reason.textContent).toMatch(/importing/i);
    expect(reason.textContent).toMatch(/CORS/i);
  });

  it('never probes a /platform/v1/* read — only the fast liveness endpoint', async () => {
    // This is the constraint that makes the strip usable during a cold start.
    // Asserted on the recorded URLs, not on the rendered text, so it cannot
    // pass while the component quietly starts reading an expensive endpoint.
    const { requested } = stubLiveness(['ok']);
    render(<PlatformBackendStatus />);
    await settle();

    expect(requested.length).toBeGreaterThan(0);
    for (const url of requested) {
      expect(url).toContain('/health');
      expect(url).not.toContain('/platform/v1/');
    }
  });

  it('stops re-probing once the backend is ready', async () => {
    const { fetchMock } = stubLiveness(['ok']);
    render(<PlatformBackendStatus pollIntervalMs={10} />);
    await settle();
    await new Promise((r) => setTimeout(r, 120));
    const callsAfterReady = fetchMock.mock.calls.length;
    // A ready indicator must not keep polling: the console's data queries own
    // their own refresh, and a permanent poll is a second, silent problem.
    expect(callsAfterReady).toBe(1);
  });

  it('keeps re-probing while the backend is still starting', async () => {
    // This is what promotes `starting` -> `ready` without an operator action.
    const { fetchMock } = stubLiveness(['timeout', 'ok']);
    render(<PlatformBackendStatus livenessTimeoutMs={20} pollIntervalMs={10} />);
    await settle();
    await new Promise((r) => setTimeout(r, 200));

    expect(fetchMock.mock.calls.length).toBeGreaterThan(1);
    expect(
      screen.getByTestId('platform-backend-status').getAttribute('data-backend-status'),
    ).toBe('ready');
  });

  it('renders the pre-probe state as CHECKING, not as a failure', () => {
    // Initial state: `unknown`. It must not flash "unavailable" on every page
    // load while the first 4 ms probe is in flight.
    render(<PlatformBackendStatus enabled={false} />);
    const strip = screen.getByTestId('platform-backend-status');
    expect(strip.getAttribute('data-backend-status')).toBe('unknown');
    expect(screen.getByTestId('platform-backend-status-value').textContent).toContain('CHECKING');
  });

  it('is announced to assistive technology as live status', () => {
    render(<PlatformBackendStatus enabled={false} />);
    const strip = screen.getByTestId('platform-backend-status');
    expect(strip.getAttribute('role')).toBe('status');
    expect(strip.getAttribute('aria-live')).toBe('polite');
  });
});