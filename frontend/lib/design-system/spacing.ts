/**
 * Design System Spacing - Stage 8E Financial OS Visual Language
 *
 * 8px spacing system. All layouts must align to a strict grid.
 * No arbitrary padding values.
 */

export const spacing = {
  0: '0px',
  0.5: '2px',
  1: '4px',
  1.5: '6px',
  2: '8px',
  2.5: '10px',
  3: '12px',
  3.5: '14px',
  4: '16px',
  5: '20px',
  6: '24px',
  7: '28px',
  8: '32px',
  9: '36px',
  10: '40px',
  11: '44px',
  12: '48px',
  14: '56px',
  16: '64px',
  20: '80px',
  24: '96px',
  28: '112px',
  32: '128px',
} as const;

export type SpacingToken = keyof typeof spacing;

// ===== Layout Constants =====
export const LEFT_RAIL_WIDTH = 180;
export const COMMAND_BAR_HEIGHT = 44;
export const TIMELINE_HEIGHT = 88;
export const STATUS_BAR_HEIGHT = 20;
export const INSPECTOR_MIN = 280;
export const INSPECTOR_MAX = 420;
export const GRID_GAP = spacing[4];

export const layoutConstants = {
  LEFT_RAIL_WIDTH,
  COMMAND_BAR_HEIGHT,
  TIMELINE_HEIGHT,
  STATUS_BAR_HEIGHT,
  INSPECTOR_MIN,
  INSPECTOR_MAX,
  GRID_GAP,
} as const;

// ===== Spacing Utilities =====
export const px = (value: number): string => `${value}px`;

export const spacingPx = {
  0: 0,
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  2.5: 10,
  3: 12,
  3.5: 14,
  4: 16,
  5: 20,
  6: 24,
  7: 28,
  8: 32,
  9: 36,
  10: 40,
  11: 44,
  12: 48,
  14: 56,
  16: 64,
  20: 80,
  24: 96,
  28: 112,
  32: 128,
} as const;