'use client';

/**
 * useWorkspaceRegistration - Auto-registers a workspace with the runtime on mount.
 * Pages call this once to declare their workspace identity.
 */

import { useEffect, useMemo, useRef } from 'react';
import { workspaceRuntime } from './workspace-runtime';
import { navigationRuntime } from './navigation-runtime';
import type { WorkspaceName, WorkspaceConfig, SurfaceType } from './runtime-types';

export interface WorkspaceRegistrationOptions {
  name: WorkspaceName;
  label?: string;
  icon?: string;
  deepLink?: string;
  defaultSurface?: SurfaceType;
  supportedCommands?: string[];
  supportedFilters?: string[];
  supportedSelections?: string[];
}

export function useWorkspaceRegistration(opts: WorkspaceRegistrationOptions) {
  const registered = useRef(false);

  // The registration config is derived once from the first render's options,
  // mirroring the previous `useRef` initialiser semantics. `useMemo` is used
  // instead of a ref because the value is read during render, and reading
  // `ref.current` during render is unsafe (react-hooks/refs).
  const config = useMemo<WorkspaceConfig>(
    () => ({
      name: opts.name,
      label: opts.label ?? opts.name.charAt(0).toUpperCase() + opts.name.slice(1),
      icon: opts.icon ?? 'circle',
      deepLink: opts.deepLink ?? `/${opts.name}`,
      defaultSurface: opts.defaultSurface ?? 'TABLE',
      supportedCommands: opts.supportedCommands ?? [],
      supportedFilters: opts.supportedFilters ?? [],
      supportedSelections: opts.supportedSelections ?? [],
    }),
    // Registration is intentionally captured once, matching the prior
    // useRef-initialiser behaviour: a workspace declares its identity on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  useEffect(() => {
    if (registered.current) return;
    registered.current = true;

    workspaceRuntime.registerWorkspace(config);

    // Set current workspace and navigation entry
    const title = config.label;
    workspaceRuntime.setTitle(title);
    workspaceRuntime.setBreadcrumbs([title]);
    navigationRuntime.pushPath(config.deepLink, config.name);

    return () => {
      // No-op on unmount — navigation history is preserved
    };
  }, [config]);

  return config;
}
