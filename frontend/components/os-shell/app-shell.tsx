/**
 * App Shell - Stage 8A Financial Operating System Shell
 *
 * Main application shell that composes all OS Shell components.
 * This is the permanent shell that every workspace will run inside.
 * No business logic. No financial calculations. No API changes.
 */

'use client';

import type { ReactNode } from 'react';
import { ShellProvider } from './shell-provider';
import { LeftRail } from './left-rail';
import { TopCommandBar } from './top-command-bar';
import { WorkspaceContainer } from './workspace-container';
import { RightInspector } from './right-inspector';
import { BottomTimeline } from './bottom-timeline';
import { BottomStatusBar } from './bottom-status-bar';
import { ResizableLayout } from './resizable-layout';

// ===== App Shell Component =====
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <ShellProvider>
      <ResizableLayout>
        {/* Left Rail - Navigation (180px) */}
        <LeftRail />

        {/* Top Command Bar - Global controls (44px) */}
        <TopCommandBar />

        {/* Workspace Container - Main content area */}
        <WorkspaceContainer>
          {children}
        </WorkspaceContainer>

        {/* Right Inspector - Context panel (280-420px) */}
        <RightInspector />

        {/* Bottom Timeline - Chronological view (88px) */}
        <BottomTimeline />

        {/* Bottom Status Bar - Runtime status (20px) */}
        <BottomStatusBar />
      </ResizableLayout>
    </ShellProvider>
  );
}
