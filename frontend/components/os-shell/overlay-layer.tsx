/**
 * Overlay Layer - Stage 8A Financial Operating System Shell
 *
 * Manages non-modal overlays: command palette, graph exploration,
 * insight detail panels, search results dropdown, notification toasts.
 * Stacked by priority (higher = on top).
 * z-index: 1000+.
 * No business logic — pure composition layer.
 */

'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { GraphOverlay } from '@/components/graph/graph-overlay';

// ===== Overlay Types =====
export type OverlayType =
  | 'command-palette'
  | 'graph-exploration'
  | 'insight-detail'
  | 'search-results'
  | 'notification-toast';

export interface OverlayRequest {
  id: string;
  type: OverlayType;
  priority: number;
  dismissible: boolean;
  props?: Record<string, unknown>;
}

// ===== Overlay Store (module-level singleton) =====
let _overlays: OverlayRequest[] = [];
const _listeners = new Set<() => void>();

function notify() {
  _listeners.forEach(fn => fn());
}

export const overlayStore = {
  request: (req: OverlayRequest) => {
    _overlays = [..._overlays, req].sort((a, b) => b.priority - a.priority);
    notify();
  },
  dismiss: (id: string) => {
    _overlays = _overlays.filter(o => o.id !== id);
    notify();
  },
  dismissAll: () => {
    _overlays = [];
    notify();
  },
  getOverlays: () => _overlays,
  subscribe: (fn: () => void) => {
    _listeners.add(fn);
    return () => { _listeners.delete(fn); };
  },
};

// ===== Overlay Renderer =====
function renderOverlayContent(overlay: OverlayRequest): React.ReactNode {
  const { type, props } = overlay;

  if (type === 'graph-exploration') {
    const scope = props?.scope as import('@/lib/graph/graph-invocation').GraphScope | undefined;
    const initialResult = props?.initialResult as import('@/lib/graph/types').GraphResult | undefined;
    if (!scope) return null;
    return (
      <GraphOverlay
        scope={scope}
        initialResult={initialResult ?? null}
        onDismiss={() => overlayStore.dismiss(overlay.id)}
      />
    );
  }

  // Fallback: try registered dynamic component
  const DynamicComponent = (overlayStore as unknown as Record<string, unknown>)[`_${type}`] as React.ComponentType<Record<string, unknown>> | undefined;
  if (DynamicComponent && props) {
    return <DynamicComponent {...props} />;
  }
  return null;
}

// ===== Overlay Layer Component =====
interface OverlayLayerProps {
  className?: string;
}

export function OverlayLayer({ className }: OverlayLayerProps) {
  const [overlays, setOverlays] = useState<OverlayRequest[]>([]);

  useEffect(() => {
    const unsubscribe = overlayStore.subscribe(() => {
      setOverlays(overlayStore.getOverlays());
    });
    return unsubscribe;
  }, []);

  if (overlays.length === 0) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 z-[1000]',
        'pointer-events-none',
        className,
      )}
    >
      {overlays.map((overlay) => (
        <div
          key={overlay.id}
          className="absolute inset-0 pointer-events-auto"
          style={{ zIndex: overlay.priority }}
        >
          {renderOverlayContent(overlay)}
        </div>
      ))}
    </div>
  );
}
