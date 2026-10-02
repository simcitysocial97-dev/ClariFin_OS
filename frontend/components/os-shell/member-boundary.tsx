/**
 * Member Boundary — M10-A3
 *
 * The financial workspace and the Platform Console are two different
 * applications that share one Next.js root layout. `ShellBoundary` already
 * selects the shell by route for exactly that reason; this boundary extends the
 * same single auditable rule to the member context.
 *
 * WHY THIS EXISTS
 * ---------------
 * `MemberProvider` fetches `GET /api/v1/members` on mount, and it is mounted in
 * the root layout, so it wrapped every route — including `/platform/**`. Browser
 * captures of the console showed `GET /api/v1/members` on every single console
 * page, which breaks the invariant `app/platform/layout.tsx` states outright:
 *
 *     - No AppShell ...
 *     - No financial data or controls
 *
 * A members list is financial data, and the console is required to be usable
 * BEFORE the financial application is opened. Mounting the provider for
 * standalone-console routes removes the call without removing the context, so a
 * console surface that ever asks for a member still gets a working (empty)
 * context instead of a thrown "useMember must be used within a MemberProvider".
 */

'use client';

import type { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { MemberProvider } from '@/lib/context/member-context';
import { isStandaloneConsoleRoute } from './shell-boundary';

export function MemberBoundary({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  if (isStandaloneConsoleRoute(pathname)) {
    return <>{children}</>;
  }

  return <MemberProvider>{children}</MemberProvider>;
}
