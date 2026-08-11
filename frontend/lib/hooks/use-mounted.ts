'use client';

import { useSyncExternalStore } from 'react';

/**
 * Returns `false` during SSR and the first client render, then `true` once the
 * component has mounted on the client.
 *
 * Implemented with `useSyncExternalStore` rather than the classic
 * `useState(false)` + `useEffect(() => setMounted(true))` pattern so that no
 * state is set synchronously inside an effect (which trips
 * `react-hooks/set-state-in-effect`). The server snapshot is `false` and the
 * client snapshot is `true`.
 */
const emptySubscribe = () => () => {};

export function useMounted(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false,
  );
}
