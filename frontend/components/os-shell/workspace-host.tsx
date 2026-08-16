/**
 * Workspace Host - Stage 8B Navigation Experience
 *
 * Mounts/unmounts active workspace with full lifecycle management.
 * Implements LRU caching (max 5), cross-fade transitions (150ms),
 * state snapshot capture and restoration, and persistent workspace state.
 * Delegates to WorkspaceRuntime (source of truth) for lifecycle state.
 * No business logic — pure composition layer.
 *
 * Lifecycle: Registered → Activated → Mounted → Cached → Restored → Deactivated → Destroyed
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import type { ReactNode } from 'react';
import { workspaceRuntime } from '@/lib/runtime';
import { navigationRuntime as navRuntime } from '@/lib/runtime';
import { workspaceLifecycleManager, type TransitionState } from '@/lib/workspace/workspace-lifecycle';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import { cn } from '@/lib/utils';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

// ===== Workspace Content Wrapper =====
interface WorkspaceContentProps {
  workspaceId: WorkspaceName;
  children: ReactNode;
  isTransitioning: boolean;
  transitionPhase: 'out' | 'in';
}

function WorkspaceContent({ workspaceId, children, isTransitioning, transitionPhase }: WorkspaceContentProps) {
  return (
    <div
      className={cn(
        'absolute inset-0 h-full w-full',
        'transition-opacity duration-150 ease-out',
        isTransitioning && transitionPhase === 'out' && 'opacity-0 pointer-events-none',
        isTransitioning && transitionPhase === 'in' && 'opacity-100',
        !isTransitioning && 'opacity-100',
      )}
      data-workspace={workspaceId}
      data-lifecycle-phase={isTransitioning ? transitionPhase : 'active'}
    >
      {children}
    </div>
  );
}

// ===== Workspace Host Component =====
interface WorkspaceHostProps {
  children?: ReactNode;
  className?: string;
}

export function WorkspaceHost({ children, className }: WorkspaceHostProps) {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceName>(() => {
    return workspaceRuntime.state.current as WorkspaceName;
  });
  const [prevWorkspace, setPrevWorkspace] = useState<WorkspaceName | null>(null);
  const [transitionState, setTransitionState] = useState<TransitionState>({
    isTransitioning: false,
    fromWorkspace: null,
    toWorkspace: null,
    startTime: 0,
    duration: 150,
  });
  const [renderTick, setRenderTick] = useState(0);
  const transitionTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Handle workspace switch with lifecycle management
  const handleWorkspaceSwitch = useCallback((from: WorkspaceName, to: WorkspaceName) => {
    // Start transition
    workspaceLifecycleManager.startTransition(from, to);
    setPrevWorkspace(from);
    setTransitionState(workspaceLifecycleManager.getTransition());

    // Activate in lifecycle manager
    const { strategy, snapshot } = workspaceLifecycleManager.activate(to, from);

    if (strategy === 'restored' && snapshot) {
      // Restore state from snapshot
      if (snapshot.filters && Object.keys(snapshot.filters).length > 0) {
        workspaceRuntime.setFilters(snapshot.filters);
      }
      if (snapshot.sortConfig) {
        workspaceRuntime.setFilters({ ...workspaceRuntime.state.filters, _sortConfig: snapshot.sortConfig });
      }
    }

    // Update active workspace after a frame
    requestAnimationFrame(() => {
      setActiveWorkspace(to);
    });
  }, []);

  // Subscribe to workspace runtime changes
  useEffect(() => {
    const unsub = workspaceRuntime.subscribe(() => {
      const newState = workspaceRuntime.state.current;
      if (newState !== activeWorkspace) {
        handleWorkspaceSwitch(activeWorkspace, newState as WorkspaceName);
      }
      setRenderTick(t => t + 1);
    });
    return unsub;
  }, [activeWorkspace, handleWorkspaceSwitch]);

  // Clean up transition after duration
  useEffect(() => {
    if (!transitionState.isTransitioning) return;

    transitionTimerRef.current = setTimeout(() => {
      if (prevWorkspace) {
        workspaceLifecycleManager.deactivate(prevWorkspace);
      }
      workspaceLifecycleManager.endTransition();
      setTransitionState(workspaceLifecycleManager.getTransition());
      setPrevWorkspace(null);
    }, transitionState.duration);

    return () => {
      if (transitionTimerRef.current) {
        clearTimeout(transitionTimerRef.current);
      }
    };
  }, [transitionState.isTransitioning, transitionState.duration, prevWorkspace]);

  // Push initial path to navigation history on mount
  useEffect(() => {
    const initial = workspaceRuntime.state.current;
    const currentPath = workspaceRegistry.get(initial as WorkspaceName)?.deepLink ?? `/${initial}`;
    navRuntime.pushPath(currentPath, initial as WorkspaceName);
  }, []); // Run once on mount

  // ARIA live region
  const ariaLabel = `Workspace: ${workspaceRegistry.get(activeWorkspace)?.label ?? activeWorkspace}`;

  return (
    <div
      className={cn('relative w-full h-full overflow-hidden', className)}
      data-active-workspace={activeWorkspace}
      data-transitioning={transitionState.isTransitioning}
      key={renderTick}
    >
      {/* Previous workspace (fading out) */}
      {prevWorkspace && (
        <WorkspaceContent
          workspaceId={prevWorkspace}
          isTransitioning={transitionState.isTransitioning}
          transitionPhase="out"
        >
          {/* Workspace content rendered by Next.js routing */}
          <div className="h-full w-full" />
        </WorkspaceContent>
      )}

      {/* Active workspace (fading in or fully visible) */}
      <WorkspaceContent
        workspaceId={activeWorkspace}
        isTransitioning={transitionState.isTransitioning}
        transitionPhase="in"
      >
        {children}
      </WorkspaceContent>

      {/* ARIA live region for screen readers */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {ariaLabel}
      </div>

      {/* Transition progress indicator (subtle) */}
      {transitionState.isTransitioning && (
        <div
          className="absolute inset-0 z-10 pointer-events-none"
          style={{
            background: 'var(--surface-default)',
            opacity: 0.3,
          }}
          aria-hidden="true"
        />
      )}
    </div>
  );
}

// ===== Hook for consuming workspace host state =====
export function useWorkspaceHost() {
  const [state, setState] = useState({
    activeWorkspace: workspaceRuntime.state.current,
    isTransitioning: false,
  });

  useEffect(() => {
    const unsub = workspaceRuntime.subscribe(() => {
      setState({
        activeWorkspace: workspaceRuntime.state.current,
        isTransitioning: workspaceLifecycleManager.getTransition().isTransitioning,
      });
    });
    return unsub;
  }, []);

  return state;
}
