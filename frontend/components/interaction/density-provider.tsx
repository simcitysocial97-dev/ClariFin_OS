/**
 * Density Provider - Stage 8F Financial OS Interaction Layer
 *
 * Provides density context to the entire application.
 * Density affects tables, panels, toolbars, spacing, node size, row height, timeline, inspector.
 */

'use client';

import { createContext, useContext, useMemo, useState, useEffect } from 'react';
import type { DensityMode, DensityConfig } from '@/lib/interaction/interaction-types';

// ===== Context Types =====
interface DensityContextValue {
  mode: DensityMode;
  config: DensityConfig;
  setMode: (mode: DensityMode) => void;
}

// ===== Context =====
const DensityContext = createContext<DensityContextValue | null>(null);

// ===== Density Configurations =====
const densityConfigs: Record<DensityMode, DensityConfig> = {
  compact: {
    mode: 'compact',
    tableRowHeight: 32,
    panelPadding: 8,
    iconSize: 14,
    fontSize: 12,
  },
  comfortable: {
    mode: 'comfortable',
    tableRowHeight: 40,
    panelPadding: 12,
    iconSize: 16,
    fontSize: 14,
  },
  analytical: {
    mode: 'analytical',
    tableRowHeight: 48,
    panelPadding: 16,
    iconSize: 18,
    fontSize: 14,
  },
};

// ===== Provider =====
interface DensityProviderProps {
  children: React.ReactNode;
  defaultMode?: DensityMode;
}

export function DensityProvider({ children, defaultMode = 'comfortable' }: DensityProviderProps) {
  const [mode, setMode] = useState<DensityMode>(() => {
    if (typeof window === 'undefined') return defaultMode;
    try {
      const stored = localStorage.getItem('os-density-mode');
      return (stored as DensityMode) || defaultMode;
    } catch {
      return defaultMode;
    }
  });

  // Save to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('os-density-mode', mode);
      } catch {
        // Ignore storage errors
      }
    }
  }, [mode]);

  const config = densityConfigs[mode];

  const value = useMemo<DensityContextValue>(
    () => ({
      mode,
      config,
      setMode,
    }),
    [mode, config],
  );

  return <DensityContext.Provider value={value}>{children}</DensityContext.Provider>;
}

// ===== Hook =====
export function useDensity(): DensityContextValue {
  const context = useContext(DensityContext);
  if (!context) {
    throw new Error('useDensity must be used within DensityProvider');
  }
  return context;
}

// ===== CSS Variables =====
/**
 * Apply density CSS variables to the document
 */
export function applyDensityVariables(mode: DensityMode): void {
  const config = densityConfigs[mode];
  const root = document.documentElement;

  root.style.setProperty('--density-table-row-height', `${config.tableRowHeight}px`);
  root.style.setProperty('--density-panel-padding', `${config.panelPadding}px`);
  root.style.setProperty('--density-icon-size', `${config.iconSize}px`);
  root.style.setProperty('--density-font-size', `${config.fontSize}px`);
}