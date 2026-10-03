/**
 * M11 — the four operator-visible console states must actually render apart
 * ========================================================================
 *
 * The classifier tests (`lib/platform/__tests__/backend-status.test.ts`) prove
 * the DECISION. This file proves the operator can SEE it.
 *
 * Why that is not redundant: before M11 the console had one terminal state, so
 * every one of these four situations rendered the same
 * "DEGRADED / API UNAVAILABLE / Retry" block. An operator watching a backend
 * that was 40 s into importing `camelot`, `cv2` and `pandas` was told the API
 * was unavailable — the one message that invites a restart, at the exact moment
 * a restart destroys the warm-up and costs the full 13.8–37.8 s again.
 *
 * Each case below asserts on the rendered DOM, not on a snapshot, so copy can
 * change while the distinctions cannot.
 */

import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ApiError, ApiTimeoutError } from '@/lib/api/gateway';
import {
  classifyLiveness,
  classifyPlatformRead,
  type BackendStatusDetail,
} from '@/lib/platform/backend-status';
import {
  ConsoleEmptyState,
  ConsoleLoadingState,
  ConsoleUnavailableState,
} from '@/components/platform/console-state';

const REFUSED = new TypeError('Failed to fetch');

// These tests deliberately mount several states in one case (to compare their
// rendered text), so the shared document body must be reset between renders or
// the later assertions find the earlier component's DOM.
afterEach(() => {
  cleanup();
});

function renderTerminal(detail: BackendStatusDetail) {
  return render(
    <ConsoleUnavailableState
      heading="Platform"
      subject="No platform signals to show."
      detail={detail}
      onRetry={() => {}}
    />,
  );
}

const starting = () =>
  classifyLiveness({ served: false, error: new ApiTimeoutError('/health', 3_000), elapsedMs: 3_000 });
const unavailable = () => classifyLiveness({ served: false, error: REFUSED, elapsedMs: 2 });
const endpointFailed = () =>
  classifyPlatformRead(
    { error: new ApiTimeoutError('/platform/v1/evidence', 20_000), path: '/platform/v1/evidence' },
    true,
  );
const ready = () => classifyLiveness({ served: true, elapsedMs: 4 });

describe('console states render four distinguishable outcomes', () => {
  it('marks each terminal state with its own machine-readable state attribute', () => {
    // This is the attribute the three Playwright console specs can extend
    // without touching the pre-M11 `console-unavailable` selector contract.
    for (const [expected, detail] of [
      ['unavailable', unavailable()],
      ['starting', starting()],
      ['endpoint-failed', endpointFailed()],
    ] as const) {
      const { unmount } = renderTerminal(detail);
      const root = screen.getByTestId('console-unavailable');
      expect(root.getAttribute('data-console-state')).toBe(expected);
      unmount();
    }
  });

  it('tells WAIT from ACT in the badge, the headline and the explanation', () => {
    const texts = (['unavailable', 'starting', 'endpoint-failed'] as const).map((state) => {
      const detail =
        state === 'unavailable' ? unavailable() : state === 'starting' ? starting() : endpointFailed();
      const { unmount } = renderTerminal(detail);
      const badge = screen.getByTestId('console-status-badge').textContent ?? '';
      const headline = screen.getByTestId('console-api-unavailable').textContent ?? '';
      const explanation = screen.getByTestId('console-state-explanation').textContent ?? '';
      unmount();
      return { state, badge, headline, explanation };
    });

    // Badges must all differ — this is what the operator reads at a glance.
    expect(new Set(texts.map((t) => t.badge)).size).toBe(3);
    expect(new Set(texts.map((t) => t.headline)).size).toBe(3);
    expect(new Set(texts.map((t) => t.explanation)).size).toBe(3);

    const byState = Object.fromEntries(texts.map((t) => [t.state, t]));

    // The starting state must tell the operator to WAIT, and must say what is
    // happening, so a 20 s banner is not mistaken for a hang.
    expect(byState.starting.badge).toContain('BACKEND STARTING');
    expect(byState.starting.headline).toMatch(/WAIT, DO NOT RESTART/);
    expect(byState.starting.explanation).toMatch(/still building|expected to finish/i);

    // The unavailable state must tell the operator to ACT.
    expect(byState.unavailable.badge).toContain('BACKEND UNAVAILABLE');
    expect(byState.unavailable.headline).toContain('API UNAVAILABLE');

    // The endpoint-failed state must NOT offer "the backend is still booting" as
    // an explanation — the liveness probe already answered.
    expect(byState['endpoint-failed'].badge).toContain('PLATFORM ENDPOINT FAILED');
    expect(byState['endpoint-failed'].explanation).toMatch(/not a cold start/i);
    expect(byState['endpoint-failed'].explanation).not.toMatch(/still booting/i);
  });

  it('surfaces the classified reason and the endpoint that failed', () => {
    const { unmount } = renderTerminal(endpointFailed());
    const reason = screen.getByTestId('console-state-endpoint-failed');
    expect(reason.textContent).toContain('/platform/v1/evidence');
    expect(reason.textContent).toMatch(/stalled/i);
    unmount();

    const second = renderTerminal(starting());
    const startReason = screen.getByTestId('console-state-starting');
    expect(startReason.textContent).toContain('3000 ms');
    second.unmount();
  });

  it('exposes whether the verdict came from a deadline breach', () => {
    // A timeout is the only positive evidence that something accepted the
    // connection. Without this attribute a reader cannot tell an evidence-based
    // `starting` from a guess.
    const a = renderTerminal(starting());
    expect(
      screen.getByTestId('console-unavailable').getAttribute('data-console-timed-out'),
    ).toBe('true');
    a.unmount();

    const b = renderTerminal(unavailable());
    expect(
      screen.getByTestId('console-unavailable').getAttribute('data-console-timed-out'),
    ).toBe('false');
    b.unmount();
  });

  it('offers a retry on every terminal state, labelled for what retrying means', () => {
    const a = renderTerminal(starting());
    // "Check again", not "Retry": retrying a starting backend by restarting it
    // is the failure mode this whole milestone exists to prevent.
    expect(screen.getByTestId('console-retry').textContent).toContain('Check again');
    a.unmount();

    const b = renderTerminal(unavailable());
    expect(screen.getByTestId('console-retry').textContent).toContain('Retry');
    b.unmount();
  });

  it('never renders a terminal state for a healthy backend', () => {
    // `ready` must not be renderable as a failure: the console shows live data
    // instead. The component returns null for `ready`/`unknown` rather than
    // collapsing them into `unavailable`, because "API UNAVAILABLE" under a
    // 200 from `GET /health` is the single worst thing this console could say.
    const detail = ready();
    expect(detail.status).toBe('ready');
    const { container } = renderTerminal(detail as BackendStatusDetail);
    expect(container.innerHTML).toBe('');
    expect(screen.queryByTestId('console-unavailable')).toBeNull();
  });

  it('preserves the pre-M11 selector contract so the existing console specs still resolve', () => {
    // platform-dashboard.spec.ts, platform-c67.2.spec.ts and
    // m10-agent3-console.spec.ts all wait for `[data-testid="console-unavailable"]`
    // as "the console reached a terminal state", and m10-agent3 additionally
    // asserts a visible /retry/i control. Widening or renaming these would
    // silently change what those specs assert.
    for (const detail of [unavailable(), starting(), endpointFailed()]) {
      const { unmount } = renderTerminal(detail);
      expect(screen.getByTestId('console-unavailable')).toBeTruthy();
      expect(screen.getByTestId('console-api-unavailable')).toBeTruthy();
      expect(screen.getByTestId('console-retry')).toBeTruthy();
      unmount();
    }
  });

  it('keeps the loading and empty states distinct from all four terminal states', () => {
    // "Still working" and "not working" must never share a rendering. The
    // original M9 defect was precisely that the dashboard had no way to say
    // "cannot work".
    const loading = render(<ConsoleLoadingState />);
    expect(screen.getByTestId('console-loading')).toBeTruthy();
    expect(screen.queryByTestId('console-unavailable')).toBeNull();
    loading.unmount();

    const empty = render(<ConsoleEmptyState heading="Workflows" subject="None." />);
    expect(screen.getByTestId('console-empty')).toBeTruthy();
    expect(screen.queryByTestId('console-loading')).toBeNull();
    empty.unmount();

    renderTerminal(unavailable());
    expect(screen.getByTestId('console-unavailable')).toBeTruthy();
    expect(screen.queryByTestId('console-loading')).toBeNull();
    expect(screen.queryByTestId('console-empty')).toBeNull();
  });

  it('does not echo a serialised error object to the operator', () => {
    // m10-agent3-console.spec.ts asserts the console never renders `"transient"`
    // or `API 404 /platform`. The reason string comes from the classifier, which
    // formats it; the raw ApiError body must not reach the DOM.
    const detail = classifyPlatformRead(
      { error: new ApiError(404, '/platform/v1/capabilities/x', '{"transient":false}'), path: '/platform/v1/capabilities/x' },
      true,
    );
    const { unmount } = renderTerminal(detail);
    const text = document.body.textContent ?? '';
    expect(text).not.toContain('"transient"');
    expect(text).not.toContain('API 404 /platform');
    unmount();
  });
});