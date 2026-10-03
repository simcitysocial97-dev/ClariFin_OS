/**
 * Add Investment Form - Stage 4 Investments Intelligence Workspace
 *
 * The user action for `POST /api/v1/investments`.
 *
 * Why this exists
 * ---------------
 * The endpoint returned HTTP 500 for every valid payload (four stacked backend
 * defects, fixed in M11), and the workspace had no way to create a holding at
 * all: `useCreateInvestment` existed with no caller, and the empty state offered
 * only "Clear filters", which cannot help when the portfolio is empty because
 * nothing has been added. The mutation chain was therefore unvalidated by any
 * user path.
 *
 * Money handling
 * --------------
 * Amounts are entered in RUPEES by a person and stored in PAISE by the
 * authority. This is the one place the conversion happens, it is the canonical
 * paise -> INR direction used everywhere else (`lib/utils/format`), and no
 * arithmetic is performed on the amounts here: the form submits integers in
 * paise and the backend computes returns.
 *
 * `investment_type` is the backend's canonical `InvestmentType` vocabulary. It
 * is not a free-text field, because the read contract
 * (`InvestmentSummaryDTO.type`) is a closed enum and a value outside it is
 * rejected with a 422 — offering arbitrary text here would only produce an
 * error the user cannot act on.
 *
 * Architecture Flow: User action → hook mutation → API → DB → cache invalidation → workspace re-render
 */

'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, X } from 'lucide-react';
import { INVESTMENT_TYPES } from '@/lib/schemas/investments';
import type { InvestmentType } from '@/types/investments-view-model';

/**
 * Add Investment Props
 */
interface AddInvestmentFormProps {
  /** Perform the mutation. Resolves when the holding has been persisted. */
  onCreate: (input: AddInvestmentInput) => Promise<unknown>;
  /** True while the mutation is in flight. */
  pending: boolean;
  /** Present when the last attempt failed. */
  error: string | null;
  /** Dismiss the form. */
  onCancel: () => void;
}

/** The values the form collects, in the shape the API accepts. */
export interface AddInvestmentInput {
  name: string;
  investment_type: InvestmentType;
  invested_paise: number;
  current_value_paise: number;
  units?: number;
  as_of_date: string;
  notes?: string;
}

/** Today as YYYY-MM-DD, the `as_of_date` format the API expects. */
function today(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${now.getFullYear()}-${month}-${day}`;
}

/**
 * Parse a rupee amount into integer paise.
 *
 * @returns paise, or null when the input is not a non-negative amount.
 */
export function rupeesToPaise(input: string): number | null {
  const trimmed = input.trim();
  if (trimmed === '') return null;
  const rupees = Number(trimmed);
  if (!Number.isFinite(rupees) || rupees < 0) return null;
  return Math.round(rupees * 100);
}

/**
 * Add Investment Form Component
 */
export function AddInvestmentForm({ onCreate, pending, error, onCancel }: AddInvestmentFormProps) {
  const [name, setName] = useState('');
  const [investmentType, setInvestmentType] = useState<InvestmentType>('mutual_funds');
  const [invested, setInvested] = useState('');
  const [currentValue, setCurrentValue] = useState('');
  const [units, setUnits] = useState('');
  const [notes, setNotes] = useState('');
  const [validation, setValidation] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (name.trim() === '') {
      setValidation('A name is required.');
      return;
    }
    const investedPaise = rupeesToPaise(invested);
    if (investedPaise === null) {
      setValidation('Invested amount must be a number of rupees, zero or more.');
      return;
    }
    const currentPaise = rupeesToPaise(currentValue);
    if (currentPaise === null) {
      setValidation('Current value must be a number of rupees, zero or more.');
      return;
    }
    const parsedUnits = units.trim() === '' ? undefined : Number(units);
    if (parsedUnits !== undefined && (!Number.isFinite(parsedUnits) || parsedUnits < 0)) {
      setValidation('Units must be a number, zero or more.');
      return;
    }
    setValidation(null);

    await onCreate({
      name: name.trim(),
      investment_type: investmentType,
      invested_paise: investedPaise,
      current_value_paise: currentPaise,
      units: parsedUnits,
      as_of_date: today(),
      notes: notes.trim() === '' ? undefined : notes.trim(),
    });
  };

  const inputClass = 'w-full border rounded px-2 py-1 text-sm';

  return (
    <Card data-testid="add-investment-form">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add investment
          </span>
          <Button variant="ghost" size="sm" onClick={onCancel} aria-label="Cancel">
            <X className="h-4 w-4" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <label className="text-sm">
              Name
              <input
                className={inputClass}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nifty 50 Index Fund"
                aria-label="Investment name"
              />
            </label>
            <label className="text-sm">
              Type
              <select
                className={inputClass}
                value={investmentType}
                onChange={(e) => setInvestmentType(e.target.value as InvestmentType)}
                aria-label="Investment type"
              >
                {INVESTMENT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              Invested (₹)
              <input
                className={inputClass}
                value={invested}
                onChange={(e) => setInvested(e.target.value)}
                inputMode="decimal"
                placeholder="100000"
                aria-label="Invested amount in rupees"
              />
            </label>
            <label className="text-sm">
              Current value (₹)
              <input
                className={inputClass}
                value={currentValue}
                onChange={(e) => setCurrentValue(e.target.value)}
                inputMode="decimal"
                placeholder="125000"
                aria-label="Current value in rupees"
              />
            </label>
            <label className="text-sm">
              Units (optional)
              <input
                className={inputClass}
                value={units}
                onChange={(e) => setUnits(e.target.value)}
                inputMode="decimal"
                placeholder="12.5"
                aria-label="Units held"
              />
            </label>
            <label className="text-sm">
              Notes (optional)
              <input
                className={inputClass}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                aria-label="Notes"
              />
            </label>
          </div>

          {(validation || error) && (
            <p className="text-sm text-[var(--color-negative-600)]" role="alert" data-testid="add-investment-error">
              {validation ?? error}
            </p>
          )}

          <Button type="submit" disabled={pending} data-testid="add-investment-submit">
            {pending ? 'Saving…' : 'Save investment'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}