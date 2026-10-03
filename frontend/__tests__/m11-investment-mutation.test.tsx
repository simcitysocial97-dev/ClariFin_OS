/**
 * M11 — the investments create mutation, end to end from the UI.
 *
 * Defect under regression
 * -----------------------
 * `POST /api/v1/investments` returned HTTP 500 for every valid payload (four
 * stacked backend defects, fixed in M11), and the workspace had no create
 * affordance at all: `useCreateInvestment` had no caller and the empty state
 * offered only "Clear filters". The mutation chain therefore had no user path,
 * which is how a permanently-500 endpoint went unnoticed.
 *
 * What this exercises
 * -------------------
 * user action -> form -> hook mutation -> POST body -> cache invalidation ->
 * re-rendered holdings table. The backend round trip and the DB are covered by
 * `backend/tests/integration/cross_layer/test_journey_investment_mutation.py`;
 * here the point is that the browser sends the fields the authority accepts and
 * that a rejection is shown rather than swallowed.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AddInvestmentForm, rupeesToPaise } from '@/components/investments/add-investment-form';
import { InvestmentsEmptyState } from '@/components/investments/empty-state';
import { InvestmentsResponseSchema, INVESTMENT_TYPES } from '@/lib/schemas/investments';

const fetchMock = vi.fn();

function portfolioWithHolding() {
  return {
    investments: [
      {
        id: '1',
        name: 'Nifty 50 Index Fund',
        type: 'mutual_funds',
        institution: '',
        current_value_paise: 12500000,
        invested_paise: 10000000,
        returns_paise: 2500000,
        returns_percentage: 25,
        returns_ytd_bps: 0,
        status: 'active',
      },
    ],
    total_value_paise: 12500000,
    total_invested_paise: 10000000,
    total_returns_paise: 2500000,
    investment_count: 1,
    insights: [],
    evidence_chain: null,
  };
}

function jsonResponse(body: unknown, status = 200): Response {
  const serialised = JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => JSON.parse(serialised),
    text: async () => serialised,
  } as unknown as Response;
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// ==================================================================
// Canonical vocabulary
// ==================================================================

describe('investment type vocabulary', () => {
  it('matches the backend InvestmentType Literal exactly', () => {
    // backend/src/core/dtos/investments_dto.py
    expect([...INVESTMENT_TYPES].sort()).toEqual(
      ['bonds', 'fd', 'gold', 'mutual_funds', 'other', 'ppf', 'stocks'].sort()
    );
  });

  it('the portfolio schema accepts a canonical holding', () => {
    expect(InvestmentsResponseSchema.safeParse(portfolioWithHolding()).success).toBe(true);
  });

  it('the portfolio schema rejects a type outside the vocabulary', () => {
    const corrupt = { ...portfolioWithHolding() };
    corrupt.investments[0].type = 'equity' as never;
    expect(InvestmentsResponseSchema.safeParse(corrupt).success).toBe(false);
  });

  it('the portfolio schema rejects a numeric id, which the backend no longer returns', () => {
    const corrupt = JSON.parse(JSON.stringify(portfolioWithHolding()));
    corrupt.investments[0].id = 1;
    expect(InvestmentsResponseSchema.safeParse(corrupt).success).toBe(false);
  });
});

// ==================================================================
// Rupee -> paise conversion
// ==================================================================

describe('rupeesToPaise', () => {
  it.each([
    ['0', 0],
    ['1', 100],
    ['100000', 10000000],
    ['125000.50', 12500050],
    ['0.05', 5],
    ['  250  ', 25000],
  ])('converts %s rupees to %i paise', (input, expected) => {
    expect(rupeesToPaise(input)).toBe(expected);
  });

  it.each([['', '   ', 'abc', '-5', 'NaN', '1,000']])(
    'rejects %j rather than producing a fabricated amount',
    (input) => {
      expect(rupeesToPaise(input)).toBeNull();
    }
  );
});

// ==================================================================
// The empty state must offer the create action
// ==================================================================

describe('InvestmentsEmptyState', () => {
  it('offers Add investment when nothing is recorded', () => {
    render(<InvestmentsEmptyState onAdd={() => {}} onAction={() => {}} />);
    expect(screen.getByTestId('investments-empty-add')).toBeInTheDocument();
    expect(screen.getByText(/No investments have been recorded yet/)).toBeInTheDocument();
  });

  it('does not offer Clear filters when no filter is applied', () => {
    render(<InvestmentsEmptyState onAdd={() => {}} onAction={() => {}} />);
    expect(screen.queryByTestId('investments-empty-clear-filters')).toBeNull();
  });

  it('offers Clear filters only when a filter is actually applied', () => {
    render(
      <InvestmentsEmptyState onAdd={() => {}} onAction={() => {}} hasActiveFilters />
    );
    expect(screen.getByTestId('investments-empty-clear-filters')).toBeInTheDocument();
    expect(screen.getByText(/No investment matches the current filters/)).toBeInTheDocument();
  });
});

// ==================================================================
// User action -> API
// ==================================================================

describe('AddInvestmentForm', () => {
  function renderForm(overrides: Partial<React.ComponentProps<typeof AddInvestmentForm>> = {}) {
    const onCreate = overrides.onCreate ?? vi.fn().mockResolvedValue({});
    render(
      <AddInvestmentForm
        onCreate={onCreate as never}
        pending={false}
        error={null}
        onCancel={() => {}}
        {...overrides}
      />
    );
    return { onCreate };
  }

  it('submits integer paise and the canonical type', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue({});
    renderForm({ onCreate });

    await user.type(screen.getByLabelText('Investment name'), 'Nifty 50 Index Fund');
    await user.type(screen.getByLabelText('Invested amount in rupees'), '100000');
    await user.type(screen.getByLabelText('Current value in rupees'), '125000');
    await user.type(screen.getByLabelText('Units held'), '12.5');
    await user.click(screen.getByTestId('add-investment-submit'));

    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
    const input = onCreate.mock.calls[0][0];
    expect(input).toMatchObject({
      name: 'Nifty 50 Index Fund',
      investment_type: 'mutual_funds',
      invested_paise: 10000000,
      current_value_paise: 12500000,
      units: 12.5,
    });
    expect(input.as_of_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('never sends a fractional paise amount', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue({});
    renderForm({ onCreate });

    await user.type(screen.getByLabelText('Investment name'), 'X');
    await user.type(screen.getByLabelText('Invested amount in rupees'), '100.005');
    await user.type(screen.getByLabelText('Current value in rupees'), '200');
    await user.click(screen.getByTestId('add-investment-submit'));

    await waitFor(() => expect(onCreate).toHaveBeenCalled());
    const input = onCreate.mock.calls[0][0];
    expect(Number.isInteger(input.invested_paise)).toBe(true);
    expect(Number.isInteger(input.current_value_paise)).toBe(true);
  });

  it('requires a name', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue({});
    renderForm({ onCreate });

    await user.type(screen.getByLabelText('Invested amount in rupees'), '100');
    await user.type(screen.getByLabelText('Current value in rupees'), '200');
    await user.click(screen.getByTestId('add-investment-submit'));

    expect(await screen.findByTestId('add-investment-error')).toHaveTextContent(
      'A name is required'
    );
    expect(onCreate).not.toHaveBeenCalled();
  });

  it.each([
    ['Invested amount in rupees', 'negative invested'],
    ['Current value in rupees', 'non-numeric current value'],
  ])('rejects a bad %s', async (label) => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue({});
    renderForm({ onCreate });

    await user.type(screen.getByLabelText('Investment name'), 'X');
    await user.type(screen.getByLabelText('Invested amount in rupees'), '100');
    await user.type(screen.getByLabelText('Current value in rupees'), '200');
    await user.clear(screen.getByLabelText(label));
    await user.type(screen.getByLabelText(label), 'abc');
    await user.click(screen.getByTestId('add-investment-submit'));

    expect(await screen.findByTestId('add-investment-error')).toBeInTheDocument();
    expect(onCreate).not.toHaveBeenCalled();
  });

  it('does not submit a negative amount', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue({});
    renderForm({ onCreate });

    await user.type(screen.getByLabelText('Investment name'), 'X');
    await user.type(screen.getByLabelText('Invested amount in rupees'), '-500');
    await user.type(screen.getByLabelText('Current value in rupees'), '200');
    await user.click(screen.getByTestId('add-investment-submit'));

    expect(await screen.findByTestId('add-investment-error')).toHaveTextContent(
      'zero or more'
    );
    expect(onCreate).not.toHaveBeenCalled();
  });

  it('shows the authority error verbatim instead of a generic failure', () => {
    renderForm({ error: 'Failed to create investment: HTTP 500 (HTTP 500)' });
    expect(screen.getByTestId('add-investment-error')).toHaveTextContent('HTTP 500');
  });

  it('disables submit while pending', () => {
    renderForm({ pending: true });
    expect(screen.getByTestId('add-investment-submit')).toBeDisabled();
  });

  it('offers only the canonical types', () => {
    renderForm();
    const options = Array.from(
      screen.getByLabelText('Investment type').querySelectorAll('option')
    ).map((option) => option.getAttribute('value'));
    expect(options.sort()).toEqual([...INVESTMENT_TYPES].sort());
  });
});

// ==================================================================
// The mutation through the hook: POST body and cache invalidation
// ==================================================================

describe('useCreateInvestment', () => {
  async function submitThroughHook() {
    const user = userEvent.setup();
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });

    // Seed the investments query so invalidation has something to refresh.
    fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
      if (init?.method === 'POST') {
        return jsonResponse({
          id: '1',
          name: 'Nifty 50 Index Fund',
          investment_type: 'mutual_funds',
          units: 12.5,
          buy_price_paise: null,
          current_price_paise: null,
          invested_paise: 10000000,
          current_value_paise: 12500000,
          as_of_date: '2026-10-02',
          is_active: 1,
          notes: null,
        });
      }
      if (String(url).includes('/api/v1/investments')) {
        return jsonResponse(portfolioWithHolding());
      }
      return jsonResponse({}, 404);
    });

    const { useCreateInvestment, useInvestments } = await import('@/lib/hooks/use-investments');

    // Success is observed through the DOM rather than captured out of the hook:
    // assigning to a variable declared outside the component is a render-phase
    // side effect (react-hooks/globals), so the harness renders the mutation's
    // own state instead.
    function Harness() {
      const mutation = useCreateInvestment();
      // Mount the read the workspace renders from, so the invalidation that
      // follows a successful mutation is observable rather than asserted about
      // a query that was never mounted.
      useInvestments();
      return (
        <>
          <button
            type="button"
            onClick={() =>
              mutation.mutate({
                name: 'Nifty 50 Index Fund',
                investment_type: 'mutual_funds',
                invested_paise: 10000000,
                current_value_paise: 12500000,
                as_of_date: '2026-10-02',
                units: 12.5,
              })
            }
          >
            create
          </button>
          <span data-testid="mutation-state">
            {mutation.isPending ? 'pending' : mutation.isSuccess ? 'success' : mutation.isError ? 'error' : 'idle'}
          </span>
        </>
      );
    }

    render(
      <QueryClientProvider client={client}>
        <Harness />
      </QueryClientProvider>
    );

    await user.click(screen.getByText('create'));
    await waitFor(() =>
      expect(screen.getByTestId('mutation-state')).toHaveTextContent('success')
    );
    await waitFor(() => expect(client.getQueryState(['investments'])).toBeDefined());
    return { client };
  }

  it('POSTs to the registered path with the documented fields', async () => {
    await submitThroughHook();

    const postCall = fetchMock.mock.calls.find(
      (call) => (call[1] as RequestInit | undefined)?.method === 'POST'
    );
    expect(postCall).toBeDefined();
    const [url, init] = postCall as [string, RequestInit];
    expect(url).toContain('/api/v1/investments');
    expect(JSON.parse(String(init.body))).toEqual({
      name: 'Nifty 50 Index Fund',
      investment_type: 'mutual_funds',
      invested_paise: 10000000,
      current_value_paise: 12500000,
      as_of_date: '2026-10-02',
      units: 12.5,
    });
  });

  it('invalidates the investments cache so the table re-reads', async () => {
    // `invalidateQueries({queryKey: ['investments']})` prefix-matches, which is
    // how it reaches the workspace query `['investments', queryParams]` that
    // renders the holdings table. The observable consequence is a second read.
    await submitThroughHook();

    const readCalls = () =>
      fetchMock.mock.calls.filter(
        (call) =>
          (call[1] as RequestInit | undefined)?.method === undefined &&
          String(call[0]).includes('/api/v1/investments')
      ).length;

    await waitFor(() => expect(readCalls()).toBeGreaterThanOrEqual(2));
  });

  it('reports a 422 with the authority detail, not a generic message', async () => {
    fetchMock.mockImplementation(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'POST') {
        return jsonResponse(
          {
            detail: [
              { loc: ['body', 'investment_type'], msg: 'Input should be a valid enum value' },
            ],
          },
          422
        );
      }
      return jsonResponse(portfolioWithHolding());
    });

    const { useCreateInvestment } = await import('@/lib/hooks/use-investments');
    const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });

    function Harness() {
      const mutation = useCreateInvestment();
      return (
        <>
          <button
            type="button"
            onClick={() =>
              mutation.mutate({
                name: 'X',
                investment_type: 'mutual_funds',
                invested_paise: 100,
                current_value_paise: 200,
                as_of_date: '2026-10-02',
              })
            }
          >
            create
          </button>
          {mutation.error && <span role="alert">{mutation.error.message}</span>}
        </>
      );
    }

    render(
      <QueryClientProvider client={client}>
        <Harness />
      </QueryClientProvider>
    );

    await userEvent.setup().click(screen.getByText('create'));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
    expect(screen.getByRole('alert').textContent).toContain('body.investment_type');
    expect(screen.getByRole('alert').textContent).toContain('valid enum value');
  });
});