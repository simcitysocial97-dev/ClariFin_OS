/**
 * Design System Elevations - Stage 8E Financial OS Visual Language
 *
 * Subtle elevation for surface hierarchy.
 * No decorative shadows. Only functional depth.
 */

export const elevations = {
  none: {
    shadow: 'none',
    description: 'No elevation — default surface',
  },
  raised: {
    shadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    description: 'Subtle lift for interactive surfaces',
  },
  interactive: {
    shadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    description: 'Hover state on raised surfaces',
  },
  selected: {
    shadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    description: 'Selected/active state',
  },
  floating: {
    shadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    description: 'Dropdowns, popovers, tooltips',
  },
  overlay: {
    shadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    description: 'Modals, drawers',
  },
} as const;

export type Elevation = keyof typeof elevations;

export const elevationClasses: Record<Elevation, string> = {
  none: '',
  raised: 'shadow-sm',
  interactive: 'shadow-md',
  selected: 'shadow-lg',
  floating: 'shadow-xl',
  overlay: 'shadow-2xl',
};