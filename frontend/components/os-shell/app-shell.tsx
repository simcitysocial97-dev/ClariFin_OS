/**
 * App Shell - Stage 8B Navigation Experience
 *
 * Main application shell that composes all OS Shell components.
 * Includes deep linking sync, workspace lifecycle, and navigation history.
 * No business logic. No financial calculations. No API changes.
 */

'use client';

import type { ReactNode } from 'react';
import { Suspense } from 'react';
import { ShellProvider } from './shell-provider';
import { LeftRail } from './left-rail';
import { TopCommandBar } from './top-command-bar';
import { WorkspaceContainer } from './workspace-container';
import { WorkspaceHost } from './workspace-host';
import { RightInspector } from './right-inspector';
import { BottomTimeline } from './bottom-timeline';
import { BottomStatusBar } from './bottom-status-bar';
import { BottomIntelligenceShelf } from './bottom-intelligence-shelf';
import { OverlayLayer } from './overlay-layer';
import { ModalLayer } from './modal-layer';
import { ResizableLayout } from './resizable-layout';
import { DeepLinkSync } from './deep-link-sync';

// ===== App Shell Component =====
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <ShellProvider>
      {/* Deep link sync — wires Next.js router to NavigationRuntime.
          DeepLinkSync calls useSearchParams(), which forces client-side
          bailout during prerendering, so it must sit inside a Suspense
          boundary. It renders nothing, hence the null fallback. */}
      <Suspense fallback={null}>
        <DeepLinkSync />
      </Suspense>

      <ResizableLayout>
        {/* Left Rail - Navigation (180px) */}
        <LeftRail />

        {/* Top Command Bar - Global controls + breadcrumbs (44px) */}
        <TopCommandBar />

        {/* Workspace Host - Lifecycle management + transitions */}
        <WorkspaceContainer>
          <WorkspaceHost>
            {children}
          </WorkspaceHost>
        </WorkspaceContainer>

        {/* Right Inspector - Context panel (280-420px) */}
        <RightInspector />

        {/* Bottom Timeline - Chronological view (88px) */}
        <BottomTimeline />

        {/* Bottom Intelligence Shelf - Passive insights */}
        <BottomIntelligenceShelf />

        {/* Bottom Status Bar - Runtime status (24px) */}
        <BottomStatusBar />

        {/* Overlay Layer - z-index: 1000+ */}
        <OverlayLayer />

        {/* Modal Layer - z-index: 2000+ */}
        <ModalLayer />
      </ResizableLayout>
    </ShellProvider>
  );
}
