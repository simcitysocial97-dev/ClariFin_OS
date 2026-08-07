/**
 * Design System Tokens - Stage 8C Financial OS Visual System
 *
 * Core design tokens for the Financial Operating System.
 * All values are in paise (₹1.00 = 100 paise) for financial determinism.
 */

// ===== Border Radius =====
export const borderRadius = {
  none: '0px',
  sm: '2px',
  md: '4px',
  lg: '6px',
  xl: '8px',
  '2xl': '12px',
  full: '9999px',
} as const;

// ===== Border Width =====
export const borderWidth = {
  0: '0px',
  1: '1px',
  2: '2px',
  4: '4px',
} as const;

// ===== Opacity =====
export const opacity = {
  0: '0',
  25: '0.25',
  50: '0.5',
  75: '0.75',
  80: '0.8',
  90: '0.9',
  100: '1',
} as const;

// ===== Z-Index =====
export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  fixed: 1200,
  modal: 1300,
  popover: 1400,
  tooltip: 1500,
  notification: 1600,
} as const;

// ===== Duration =====
export const duration = {
  instant: '0ms',
  fastest: '50ms',
  faster: '100ms',
  fast: '150ms',
  normal: '200ms',
  slow: '300ms',
  slower: '400ms',
  slowest: '500ms',
} as const;

// ===== Easing =====
export const easing = {
  linear: 'linear',
  in: 'cubic-bezier(0.4, 0, 1, 1)',
  out: 'cubic-bezier(0, 0, 0.2, 1)',
  inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
} as const;

// ===== Font Family =====
export const fontFamily = {
  sans: 'var(--font-sans, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif)',
  mono: 'var(--font-mono, "SF Mono", "Fira Code", "Roboto Mono", monospace)',
  display: 'var(--font-display, "IBM Plex Sans", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif)',
} as const;

// ===== Font Size =====
export const fontSize = {
  xs: '0.75rem', // 12px
  sm: '0.875rem', // 14px
  md: '1rem', // 16px
  lg: '1.125rem', // 18px
  xl: '1.25rem', // 20px
  '2xl': '1.5rem', // 24px
  '3xl': '1.875rem', // 30px
  '4xl': '2.25rem', // 36px
} as const;

// ===== Font Weight =====
export const fontWeight = {
  regular: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
} as const;

// ===== Line Height =====
export const lineHeight = {
  none: '1',
  tight: '1.25',
  snug: '1.375',
  normal: '1.5',
  relaxed: '1.625',
  loose: '2',
} as const;

// ===== Shadow =====
export const shadow = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
} as const;

// ===== Screen Sizes =====
export const screen = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;