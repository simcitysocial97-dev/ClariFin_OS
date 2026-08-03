/**
 * useWorkspaceRegistration - Auto-registers a workspace with the runtime on mount.
 * Pages call this once to declare their workspace identity.
 */

import { useEffect, useRef } from 'react';
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
  const config = useRef<WorkspaceConfig>({
    name: opts.name,
    label: opts.label ?? opts.name.charAt(0).toUpperCase() + opts.name.slice(1),
    icon: opts.icon ?? 'circle',
    deepLink: opts.deepLink ?? `/${opts.name}`,
    defaultSurface: opts.defaultSurface ?? 'TABLE',
    supportedCommands: opts.supportedCommands ?? [],
    supportedFilters: opts.supportedFilters ?? [],
    supportedSelections: opts.supportedSelections ?? [],
  });

  useEffect(() => {
    if (registered.current) return;
    registered.current = true;

    workspaceRuntime.registerWorkspace(config.current);

    // Set current workspace and navigation entry
    const title = config.current.label;
    workspaceRuntime.setTitle(title);
    workspaceRuntime.setBreadcrumbs([title]);
    navigationRuntime.pushPath(config.current.deepLink, config.current.name);

    return () => {
      // No-op on unmount — navigation history is preserved
    };
  }, []);

  return config.current;
}
