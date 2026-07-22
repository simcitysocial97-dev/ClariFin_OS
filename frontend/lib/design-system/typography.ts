/**
 * Design System Typography - Stage 8C Financial OS Visual System
 *
 * Typography system for financial data hierarchy.
 * Monospace for values, readable for labels.
 */

import { fontFamily, fontSize, fontWeight, lineHeight } from './tokens';

// ===== Financial Typography =====
export const financialTypography = {
  // Monetary values - monospace for alignment
  value: {
    fontFamily: fontFamily.mono,
    fontSize: fontSize.md,
    fontWeight: fontWeight.medium,
    lineHeight: lineHeight.none,
    letterSpacing: '0.025em',
  },

  // Large values (net worth, totals)
  valueLarge: {
    fontFamily: fontFamily.mono,
    fontSize: fontSize.lg,
    fontWeight: fontWeight.semibold,
    lineHeight: lineHeight.none,
    letterSpacing: '0.025em',
  },

  // Small values (transaction amounts)
  valueSmall: {
    fontFamily: fontFamily.mono,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.regular,
    lineHeight: lineHeight.none,
    letterSpacing: '0.025em',
  },

  // Node labels
  nodeLabel: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
    lineHeight: lineHeight.snug,
  },

  // Node labels (small)
  nodeLabelSmall: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.xs,
    fontWeight: fontWeight.regular,
    lineHeight: lineHeight.tight,
  },

  // Section headers
  sectionHeader: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.lg,
    fontWeight: fontWeight.semibold,
    lineHeight: lineHeight.snug,
  },

  // Panel headers
  panelHeader: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.xl,
    fontWeight: fontWeight.semibold,
    lineHeight: lineHeight.snug,
  },

  // Body text
  body: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.regular,
    lineHeight: lineHeight.normal,
  },

  // Caption text
  caption: {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.xs,
    fontWeight: fontWeight.regular,
    lineHeight: lineHeight.tight,
  },
} as const;

// ===== CSS Classes =====
// Hierarchy: Financial Values → Primary Metrics → Panel Titles → Section Labels → Metadata → Captions → Hints
// Use fin-* token classes only — no arbitrary sizes, no hardcoded grays.
export const typographyClasses = {
  // Financial Values
  value: 'fin-amount',
  valueLarge: 'fin-amount-large',
  valueSmall: 'fin-amount-compact',
  // Primary Metrics / Node labels
  nodeLabel: 'fin-label',
  nodeLabelSmall: 'fin-label-caption',
  // Panel Titles
  panelHeader: 'fin-panel-header',
  // Section Labels
  sectionHeader: 'fin-section-header',
  // Body / Metadata
  body: 'fin-body',
  bodySmall: 'fin-body-small',
  // Captions / Hints
  caption: 'fin-caption',
  hint: 'fin-caption text-[var(--text-tertiary)]',
} as const;
