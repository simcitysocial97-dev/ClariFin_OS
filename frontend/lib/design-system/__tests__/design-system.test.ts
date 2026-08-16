/**
 * Design System Token Tests - Milestone 8 Visual Language
 *
 * Validates that all design tokens conform to the Financial OS Shell
 * Architecture specification (Section 8).
 */

import { describe, it, expect } from 'vitest';
import { borderRadius, borderWidth, opacity, zIndex, duration, easing, fontFamily, fontSize, fontWeight, lineHeight, shadow, screen } from '@/lib/design-system/tokens';
import { spacing, spacingPx } from '@/lib/design-system/spacing';
import { financialColors, nodeTypeColors, edgeTypeColors, confidenceColors, riskColors, uiColors } from '@/lib/design-system/colors';
import { financialTypography, typographyClasses } from '@/lib/design-system/typography';
import { densityConfig, densityClasses, DEFAULT_DENSITY, getDensityConfig, getDensityClass } from '@/lib/design-system/density';
import { elevations, elevationClasses } from '@/lib/design-system/elevations';
import { financialMotion, motionClasses, keyframes } from '@/lib/design-system/motion';
import {
  getNodeGrammar,
  getEdgeGrammar,
  getConfidenceColor,
  getRiskColor,
} from '@/lib/design-system/financial-semantics';

describe('Design System Tokens — Milestone 8', () => {
  describe('Spacing Scale (Arch 8.2)', () => {
    it('provides base unit of 4px', () => {
      expect(spacing[1]).toBe('4px');
      expect(spacingPx[1]).toBe(4);
    });

    it('provides 8px scale with half-step increments', () => {
      expect(spacing[0]).toBe('0px');
      expect(spacing[0.5]).toBe('2px');
      expect(spacing[1]).toBe('4px');
      expect(spacing[2]).toBe('8px');
      expect(spacing[4]).toBe('16px');
      expect(spacing[8]).toBe('32px');
    });

    it('provides px utility values', () => {
      expect(spacingPx[0]).toBe(0);
      expect(spacingPx[8]).toBe(32);
      expect(spacingPx[16]).toBe(64);
    });

    it('px() helper converts numbers to pixel strings', () => {
      expect(spacingPx[4]).toBe(16);
    });
  });

  describe('Border Radius (Arch 8.2)', () => {
    it('provides standard radius scale', () => {
      expect(borderRadius.none).toBe('0px');
      expect(borderRadius.sm).toBe('2px');
      expect(borderRadius.md).toBe('4px');
      expect(borderRadius.lg).toBe('6px');
      expect(borderRadius.xl).toBe('8px');
      expect(borderRadius['2xl']).toBe('12px');
      expect(borderRadius.full).toBe('9999px');
    });
  });

  describe('Border Width (Arch 8.2)', () => {
    it('provides standard width scale', () => {
      expect(borderWidth[0]).toBe('0px');
      expect(borderWidth[1]).toBe('1px');
      expect(borderWidth[2]).toBe('2px');
      expect(borderWidth[4]).toBe('4px');
    });
  });

  describe('Opacity Scale', () => {
    it('provides standard opacity values', () => {
      expect(opacity[0]).toBe('0');
      expect(opacity[50]).toBe('0.5');
      expect(opacity[100]).toBe('1');
    });
  });

  describe('Z-Index Hierarchy (Arch 8.14)', () => {
    it('provides correct z-index hierarchy', () => {
      expect(zIndex.base).toBe(0);
      expect(zIndex.dropdown).toBe(1000);
      expect(zIndex.sticky).toBe(1100);
      expect(zIndex.fixed).toBe(1200);
      expect(zIndex.modal).toBe(1300);
      expect(zIndex.popover).toBe(1400);
      expect(zIndex.tooltip).toBe(1500);
      expect(zIndex.notification).toBe(1600);
    });

    it('orders z-index values correctly', () => {
      expect(zIndex.base).toBeLessThan(zIndex.dropdown);
      expect(zIndex.dropdown).toBeLessThan(zIndex.sticky);
      expect(zIndex.sticky).toBeLessThan(zIndex.fixed);
      expect(zIndex.fixed).toBeLessThan(zIndex.modal);
      expect(zIndex.modal).toBeLessThan(zIndex.popover);
      expect(zIndex.popover).toBeLessThan(zIndex.tooltip);
      expect(zIndex.tooltip).toBeLessThan(zIndex.notification);
    });
  });

  describe('Duration Scale (Arch 8.4)', () => {
    it('provides 8-step duration scale', () => {
      expect(duration.instant).toBe('0ms');
      expect(duration.fastest).toBe('50ms');
      expect(duration.faster).toBe('100ms');
      expect(duration.fast).toBe('150ms');
      expect(duration.normal).toBe('200ms');
      expect(duration.slow).toBe('300ms');
      expect(duration.slower).toBe('400ms');
      expect(duration.slowest).toBe('500ms');
    });

    it('no animation exceeds 500ms', () => {
      const values = Object.values(duration);
      values.forEach(v => {
        const ms = parseInt(v);
        expect(ms).toBeLessThanOrEqual(500);
      });
    });
  });

  describe('Easing Curves (Arch 8.4)', () => {
    it('provides four easing curves', () => {
      expect(easing.linear).toBe('linear');
      expect(easing.in).toBe('cubic-bezier(0.4, 0, 1, 1)');
      expect(easing.out).toBe('cubic-bezier(0, 0, 0.2, 1)');
      expect(easing.inOut).toBe('cubic-bezier(0.4, 0, 0.2, 1)');
    });
  });

  describe('Font Family (Arch 8.8)', () => {
    it('provides sans and mono families', () => {
      expect(fontFamily.sans).toContain('system-ui');
      expect(fontFamily.mono).toContain('monospace');
    });

    it('provides display font family', () => {
      expect(fontFamily.display).toContain('IBM Plex Sans');
    });
  });

  describe('Font Size (Arch 8.8)', () => {
    it('provides standard font sizes', () => {
      expect(fontSize.xs).toBe('0.75rem');
      expect(fontSize.sm).toBe('0.875rem');
      expect(fontSize.md).toBe('1rem');
      expect(fontSize.lg).toBe('1.125rem');
      expect(fontSize.xl).toBe('1.25rem');
      expect(fontSize['2xl']).toBe('1.5rem');
    });
  });

  describe('Font Weight (Arch 8.8)', () => {
    it('provides standard weight values', () => {
      expect(fontWeight.regular).toBe('400');
      expect(fontWeight.medium).toBe('500');
      expect(fontWeight.semibold).toBe('600');
      expect(fontWeight.bold).toBe('700');
    });
  });

  describe('Line Height (Arch 8.8)', () => {
    it('provides standard line height values', () => {
      expect(lineHeight.none).toBe('1');
      expect(lineHeight.tight).toBe('1.25');
      expect(lineHeight.snug).toBe('1.375');
      expect(lineHeight.normal).toBe('1.5');
    });
  });

  describe('Shadow (Arch 8.3)', () => {
    it('provides shadow tokens', () => {
      expect(shadow.sm).toContain('rgb(0 0 0 / 0.05)');
      expect(shadow.md).toContain('rgb(0 0 0 / 0.1)');
      expect(shadow.lg).toContain('rgb(0 0 0 / 0.1)');
    });
  });

  describe('Screen Sizes', () => {
    it('provides standard breakpoints', () => {
      expect(screen.sm).toBe('640px');
      expect(screen.md).toBe('768px');
      expect(screen.lg).toBe('1024px');
      expect(screen.xl).toBe('1280px');
      expect(screen['2xl']).toBe('1536px');
    });
  });
});

describe('Design System Colors — Milestone 8', () => {
  describe('Financial Semantic Colors (Arch 8.6)', () => {
    it('positive color has 50-900 scale', () => {
      expect(financialColors.positive[50]).toBeDefined();
      expect(financialColors.positive[500]).toBeDefined();
      expect(financialColors.positive[900]).toBeDefined();
    });

    it('negative color has 50-900 scale', () => {
      expect(financialColors.negative[50]).toBeDefined();
      expect(financialColors.negative[500]).toBeDefined();
      expect(financialColors.negative[900]).toBeDefined();
    });

    it('warning color has 50-900 scale', () => {
      expect(financialColors.warning[50]).toBeDefined();
      expect(financialColors.warning[500]).toBeDefined();
      expect(financialColors.warning[900]).toBeDefined();
    });

    it('info color has 50-900 scale', () => {
      expect(financialColors.info[50]).toBeDefined();
      expect(financialColors.info[500]).toBeDefined();
      expect(financialColors.info[900]).toBeDefined();
    });

    it('neutral color has 50-900 scale', () => {
      expect(financialColors.neutral[50]).toBeDefined();
      expect(financialColors.neutral[500]).toBeDefined();
      expect(financialColors.neutral[900]).toBeDefined();
    });

    it('positive uses green, negative uses red', () => {
      expect(financialColors.positive[500]).toBe('#22c55e');
      expect(financialColors.negative[500]).toBe('#ef4444');
    });
  });

  describe('Node Type Colors (Arch 8.6)', () => {
    it('provides colors for all 13 node types', () => {
      const expectedKeys = [
        'transaction', 'account', 'cashflow_month', 'cashflow_category',
        'loan', 'amortization_entry', 'credit_card', 'credit_card_statement',
        'investment', 'holding', 'behaviour_score', 'spending_pattern',
        'reconciliation_statement', 'discrepancy', 'forecast_projection',
        'forecast_scenario', 'net_worth_snapshot', 'net_worth_breakdown',
        'merchant', 'category', 'institution',
      ];
      for (const key of expectedKeys) {
        expect(nodeTypeColors[key as keyof typeof nodeTypeColors]).toBeDefined();
      }
    });
  });

  describe('Edge Type Colors (Arch 8.6)', () => {
    it('provides colors for all edge types', () => {
      expect(edgeTypeColors.belongs_to).toBeDefined();
      expect(edgeTypeColors.categorized_as).toBeDefined();
      expect(edgeTypeColors.from_merchant).toBeDefined();
      expect(edgeTypeColors.at_institution).toBeDefined();
      expect(edgeTypeColors.composes).toBeDefined();
      expect(edgeTypeColors.affects_cashflow).toBeDefined();
      expect(edgeTypeColors.amortizes).toBeDefined();
      expect(edgeTypeColors.has_statement).toBeDefined();
      expect(edgeTypeColors.has_holding).toBeDefined();
      expect(edgeTypeColors.impacts_score).toBeDefined();
      expect(edgeTypeColors.reconciles).toBeDefined();
      expect(edgeTypeColors.projects).toBeDefined();
      expect(edgeTypeColors.scenario_of).toBeDefined();
      expect(edgeTypeColors.traces_to).toBeDefined();
      expect(edgeTypeColors.references).toBeDefined();
      expect(edgeTypeColors.derived_from).toBeDefined();
      expect(edgeTypeColors.related_to).toBeDefined();
    });
  });

  describe('Confidence Colors', () => {
    it('high is green, medium is amber, low is red', () => {
      expect(confidenceColors.high).toBe(financialColors.success[500]);
      expect(confidenceColors.medium).toBe(financialColors.warning[500]);
      expect(confidenceColors.low).toBe(financialColors.negative[500]);
    });
  });

  describe('Risk Colors', () => {
    it('low is green, medium is amber, high is red, critical is darker red', () => {
      expect(riskColors.low).toBe(financialColors.success[500]);
      expect(riskColors.medium).toBe(financialColors.warning[500]);
      expect(riskColors.high).toBe(financialColors.negative[500]);
      expect(riskColors.critical).toBe(financialColors.negative[700]);
    });
  });

  describe('UI Colors', () => {
    it('provides surface, border, and text color groups', () => {
      expect(uiColors.background.primary).toBeDefined();
      expect(uiColors.background.secondary).toBeDefined();
      expect(uiColors.border.primary).toBeDefined();
      expect(uiColors.border.focus).toBeDefined();
      expect(uiColors.text.primary).toBeDefined();
      expect(uiColors.text.secondary).toBeDefined();
      expect(uiColors.text.disabled).toBeDefined();
    });
  });
});

describe('Design System Typography — Milestone 8', () => {
  describe('Typography Tokens (Arch 8.8)', () => {
    it('monetary values use monospace font', () => {
      expect(financialTypography.value.fontFamily).toContain('mono');
    });

    it('body text uses sans-serif font', () => {
      expect(financialTypography.body.fontFamily).toContain('sans');
    });

    it('provides all hierarchy levels', () => {
      expect(financialTypography.h1).toBeDefined();
      expect(financialTypography.h2).toBeDefined();
      expect(financialTypography.h3).toBeDefined();
      expect(financialTypography.value).toBeDefined();
      expect(financialTypography.valueLarge).toBeDefined();
      expect(financialTypography.valueSmall).toBeDefined();
      expect(financialTypography.nodeLabel).toBeDefined();
      expect(financialTypography.sectionHeader).toBeDefined();
      expect(financialTypography.panelHeader).toBeDefined();
      expect(financialTypography.body).toBeDefined();
      expect(financialTypography.caption).toBeDefined();
    });

    it('H1 is 24px bold for workspace title', () => {
      expect(financialTypography.h1.fontSize).toBe('1.5rem');
      expect(financialTypography.h1.fontWeight).toBe('700');
    });

    it('H2 is 20px semibold for section headings', () => {
      expect(financialTypography.h2.fontSize).toBe('1.25rem');
      expect(financialTypography.h2.fontWeight).toBe('600');
    });

    it('H3 is 16px semibold for card/panel titles', () => {
      expect(financialTypography.h3.fontSize).toBe('1rem');
      expect(financialTypography.h3.fontWeight).toBe('600');
    });

    it('monetary values use tabular numbers', () => {
      const valueTypography = financialTypography.value;
      expect(valueTypography.fontFamily).toContain('mono');
      expect(valueTypography.fontWeight).toBe('500');
    });
  });

  describe('Typography CSS Classes', () => {
    it('provides CSS class for each hierarchy level', () => {
      expect(typographyClasses.value).toBe('fin-amount');
      expect(typographyClasses.valueLarge).toBe('fin-amount-large');
      expect(typographyClasses.valueSmall).toBe('fin-amount-compact');
      expect(typographyClasses.sectionHeader).toBe('fin-section-header');
      expect(typographyClasses.panelHeader).toBe('fin-panel-header');
      expect(typographyClasses.body).toBe('fin-body');
      expect(typographyClasses.bodySmall).toBe('fin-body-small');
      expect(typographyClasses.caption).toBe('fin-caption');
      expect(typographyClasses.hint).toContain('fin-caption');
      expect(typographyClasses.h1).toBe('fin-h1');
      expect(typographyClasses.h2).toBe('fin-h2');
      expect(typographyClasses.h3).toBe('fin-h3');
    });
  });
});

describe('Design System Density — Milestone 8', () => {
  describe('Density Levels (Arch 8.7)', () => {
    it('provides three density levels', () => {
      expect(densityConfig.compact).toBeDefined();
      expect(densityConfig.comfortable).toBeDefined();
      expect(densityConfig.spacious).toBeDefined();
    });

    it('compact density has 32px row height', () => {
      expect(densityConfig.compact.rowHeight).toBe(32);
      expect(densityConfig.compact.cellPadding).toBe(4);
      expect(densityConfig.compact.fontSize).toBe(12);
    });

    it('comfortable density has 40px row height', () => {
      expect(densityConfig.comfortable.rowHeight).toBe(40);
      expect(densityConfig.comfortable.cellPadding).toBe(8);
      expect(densityConfig.comfortable.fontSize).toBe(13);
    });

    it('spacious density has 56px row height', () => {
      expect(densityConfig.spacious.rowHeight).toBe(56);
      expect(densityConfig.spacious.cellPadding).toBe(16);
      expect(densityConfig.spacious.fontSize).toBe(14);
    });

    it('default density is comfortable', () => {
      expect(DEFAULT_DENSITY).toBe('comfortable');
    });

    it('getDensityConfig returns correct config', () => {
      const config = getDensityConfig('compact');
      expect(config.rowHeight).toBe(32);
      const spaciousConfig = getDensityConfig('spacious');
      expect(spaciousConfig.rowHeight).toBe(56);
    });

    it('getDensityClass returns CSS class', () => {
      expect(getDensityClass('compact')).toBe('fin-density-compact');
      expect(getDensityClass('comfortable')).toBe('fin-density-comfortable');
      expect(getDensityClass('spacious')).toBe('fin-density-spacious');
    });

    it('density classes map to correct CSS classes', () => {
      expect(densityClasses.compact).toBe('fin-density-compact');
      expect(densityClasses.comfortable).toBe('fin-density-comfortable');
      expect(densityClasses.spacious).toBe('fin-density-spacious');
    });
  });
});

describe('Design System Elevations — Milestone 8', () => {
  describe('Elevation Scale (Arch 8.3)', () => {
    it('provides six elevation levels', () => {
      expect(elevations.none).toBeDefined();
      expect(elevations.raised).toBeDefined();
      expect(elevations.interactive).toBeDefined();
      expect(elevations.selected).toBeDefined();
      expect(elevations.floating).toBeDefined();
      expect(elevations.overlay).toBeDefined();
    });

    it('workspace content is flat (no elevation)', () => {
      expect(elevations.none.shadow).toBe('none');
    });

    it('modal has maximum elevation', () => {
      expect(elevations.overlay.shadow).toContain('0 20px 25px');
    });

    it('elevation classes map correctly', () => {
      expect(elevationClasses.none).toBe('');
      expect(elevationClasses.raised).toBe('shadow-sm');
      expect(elevationClasses.interactive).toBe('shadow-md');
      expect(elevationClasses.selected).toBe('shadow-lg');
      expect(elevationClasses.floating).toBe('shadow-xl');
      expect(elevationClasses.overlay).toBe('shadow-2xl');
    });
  });
});

describe('Design System Motion — Milestone 8', () => {
  describe('Motion Tokens (Arch 8.5)', () => {
    it('provides motion definitions for financial interactions', () => {
      expect(financialMotion.moneyTransfer).toBeDefined();
      expect(financialMotion.selection).toBeDefined();
      expect(financialMotion.risk).toBeDefined();
      expect(financialMotion.simulation).toBeDefined();
      expect(financialMotion.confidence).toBeDefined();
      expect(financialMotion.focus).toBeDefined();
      expect(financialMotion.hover).toBeDefined();
    });

    it('selection duration is 150ms', () => {
      expect(financialMotion.selection.duration).toBe('150ms');
    });

    it('hover transition uses fast duration (150ms)', () => {
      expect(financialMotion.hover.transition).toContain('150ms');
    });

    it('provides motion CSS classes', () => {
      expect(motionClasses.selectionHalo).toContain('transition');
      expect(motionClasses.hoverScale).toContain('transition');
      expect(motionClasses.focusRing).toContain('focus');
      expect(motionClasses.panelOpen).toContain('transition');
      expect(motionClasses.navigation).toBe('transition-none');
    });

    it('provides keyframes', () => {
      expect(keyframes.pulse).toContain('opacity');
      expect(keyframes.pulse).toContain('scale');
      expect(keyframes.dash).toContain('stroke-dashoffset');
    });
  });
});

describe('Design System Financial Semantics — Milestone 8', () => {
  describe('Node Grammar', () => {
    it('transaction node is circle with neutral color', () => {
      const grammar = getNodeGrammar('transaction');
      expect(grammar.shape).toBe('circle');
      expect(grammar.color).toBe(nodeTypeColors.transaction);
      expect(grammar.size).toBe(12);
    });

    it('account node is square with info color', () => {
      const grammar = getNodeGrammar('account');
      expect(grammar.shape).toBe('square');
      expect(grammar.color).toBe(nodeTypeColors.account);
    });

    it('loan node is octagon with negative color', () => {
      const grammar = getNodeGrammar('loan');
      expect(grammar.shape).toBe('octagon');
      expect(grammar.color).toBe(nodeTypeColors.loan);
    });

    it('unknown node type returns fallback', () => {
      const grammar = getNodeGrammar('unknown');
      expect(grammar.shape).toBe('circle');
      expect(grammar.color).toBe(financialColors.neutral[500]);
    });
  });

  describe('Edge Grammar', () => {
    it('projects edge has flow animation', () => {
      const grammar = getEdgeGrammar('projects');
      expect(grammar.animation).toBe('flow');
      expect(grammar.strokeDasharray).toBe('5,5');
    });

    it('belongs_to edge has no animation', () => {
      const grammar = getEdgeGrammar('belongs_to');
      expect(grammar.animation).toBe('none');
    });

    it('unknown edge type returns fallback', () => {
      const grammar = getEdgeGrammar('unknown');
      expect(grammar.strokeWidth).toBe(1);
    });
  });

  describe('Confidence and Risk Helpers', () => {
    it('getConfidenceColor returns green for high (>=80)', () => {
      expect(getConfidenceColor(80)).toBe(confidenceColors.high);
      expect(getConfidenceColor(100)).toBe(confidenceColors.high);
    });

    it('getConfidenceColor returns amber for medium (50-79)', () => {
      expect(getConfidenceColor(50)).toBe(confidenceColors.medium);
      expect(getConfidenceColor(79)).toBe(confidenceColors.medium);
    });

    it('getConfidenceColor returns red for low (<50)', () => {
      expect(getConfidenceColor(49)).toBe(confidenceColors.low);
      expect(getConfidenceColor(0)).toBe(confidenceColors.low);
    });

    it('getRiskColor maps all risk levels', () => {
      expect(getRiskColor('low')).toBe(riskColors.low);
      expect(getRiskColor('medium')).toBe(riskColors.medium);
      expect(getRiskColor('high')).toBe(riskColors.high);
      expect(getRiskColor('critical')).toBe(riskColors.critical);
    });
  });
});
