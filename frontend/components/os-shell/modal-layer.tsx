/**
 * Modal Layer - Stage 8A Financial Operating System Shell
 *
 * Manages modal dialogs: confirmations, create/edit forms,
 * import wizards, scenario configuration, reconciliation resolution.
 * Only one modal active at a time (stacking forbidden).
 * z-index: 2000+.
 * No business logic — pure composition layer.
 */

'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

// ===== Modal Types =====
export type ModalType = 'confirmation' | 'form' | 'wizard' | 'configuration';

export interface ModalRequest {
  id: string;
  title: string;
  type: ModalType;
  workspaceId?: string;
  dismissible: boolean;
  onCommit?: () => void;
  onCancel?: () => void;
  props?: Record<string, unknown>;
}

// ===== Modal Store (module-level singleton) =====
let _modal: ModalRequest | null = null;
const _listeners = new Set<() => void>();

function notify() {
  _listeners.forEach(fn => fn());
}

export const modalStore = {
  open: (req: ModalRequest) => {
    // Only one modal at a time — close any existing first
    _modal = req;
    notify();
  },
  close: () => {
    _modal = null;
    notify();
  },
  getModal: () => _modal,
  subscribe: (fn: () => void) => {
    _listeners.add(fn);
    return () => { _listeners.delete(fn); };
  },
};

// ===== Modal Layer Component =====
interface ModalLayerProps {
  className?: string;
}

export function ModalLayer({ className }: ModalLayerProps) {
  const [modal, setModal] = useState<ModalRequest | null>(null);

  useEffect(() => {
    const unsubscribe = modalStore.subscribe(() => {
      setModal(modalStore.getModal());
    });
    return unsubscribe;
  }, []);

  if (!modal) return null;

  const handleCancel = () => {
    if (modal.dismissible) {
      modal.onCancel?.();
      modalStore.close();
    }
  };

  const handleCommit = () => {
    modal.onCommit?.();
    modalStore.close();
  };

  return (
    <div
      className={cn(
        'fixed inset-0 z-[2000]',
        className,
      )}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[var(--surface-overlay)]"
        onClick={modal.dismissible ? handleCancel : undefined}
      />

      {/* Modal container */}
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div
          className={cn(
            'bg-[var(--surface-default)]',
            'border border-[var(--border-default)]',
            'rounded-[var(--radius-lg)]',
            'shadow-[var(--elevation-5)]',
            'max-w-[640px] w-full',
            'max-h-[80vh] overflow-y-auto',
            'flex flex-col',
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-default)] shrink-0">
            <h2 className="fin-h3 text-[var(--text-primary)] font-semibold">
              {modal.title}
            </h2>
            {modal.dismissible && (
              <button
                onClick={handleCancel}
                className="flex items-center justify-center h-6 w-6 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] transition-colors"
                aria-label="Close modal"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Body */}
          <div className="px-4 py-3 flex-1">
            <div className="text-[var(--text-secondary)] fin-body-small">
              {modal.type === 'confirmation' && (
                <p>{modal.props?.message as string | undefined}</p>
              )}
              {modal.type !== 'confirmation' && (
                <p>Modal content for &quot;{modal.title}&quot;</p>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-[var(--border-default)] shrink-0">
            {modal.dismissible && (
              <button
                onClick={handleCancel}
                className="px-3 py-1.5 rounded-[var(--radius-sm)] text-[var(--text-secondary)] hover:bg-[var(--surface-interactive)] fin-body-small transition-colors"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleCommit}
              className="px-3 py-1.5 rounded-[var(--radius-sm)] bg-[var(--color-selection)] text-white hover:opacity-90 fin-body-small transition-opacity"
            >
              {modal.type === 'confirmation' ? 'Confirm' : 'Submit'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
