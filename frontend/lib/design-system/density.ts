/**
 * Design System Density - Stage 8E Financial OS Visual Language
 *
 * Density levels for financial data display.
 * Aligns with Architecture Section 8.7.
 *
 * Compact: Large datasets, tables (32px rows, 4px padding, 12px font)
 * Comfortable: Default (40px rows, 8px padding, 13px font)
 * Spacious: Dashboards, cards (56px rows, 16px padding, 14px font)
 */

export type DensityLevel = 'compact' | 'comfortable' | 'spacious';

export interface DensityConfig {
  rowHeight: number;
  cellPadding: number;
  fontSize: number;
  iconSize: number;
  panelPadding: number;
}

export const densityConfig: Record<DensityLevel, DensityConfig> = {
  compact: {
    rowHeight: 32,
    cellPadding: 4,
    fontSize: 12,
    iconSize: 14,
    panelPadding: 8,
  },
  comfortable: {
    rowHeight: 40,
    cellPadding: 8,
    fontSize: 13,
    iconSize: 16,
    panelPadding: 12,
  },
  spacious: {
    rowHeight: 56,
    cellPadding: 16,
    fontSize: 14,
    iconSize: 18,
    panelPadding: 16,
  },
};

export const densityClasses: Record<DensityLevel, string> = {
  compact: 'fin-density-compact',
  comfortable: 'fin-density-comfortable',
  spacious: 'fin-density-spacious',
};

export const DEFAULT_DENSITY: DensityLevel = 'comfortable';

export function getDensityConfig(density: DensityLevel): DensityConfig {
  return densityConfig[density];
}

export function getDensityClass(density: DensityLevel): string {
  return densityClasses[density];
}
