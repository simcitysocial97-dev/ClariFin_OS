/**
 * Chart Config - Shared constants for chart configuration
 *
 * Contains duplicated constants extracted from chart implementations.
 */

/**
 * Default chart margins
 * Used across multiple chart types
 */
export const CHART_MARGINS = {
  default: { top: 20, right: 30, left: 80, bottom: 20 },
  compact: { top: 10, right: 30, left: 80, bottom: 10 },
  tight: { top: 5, right: 10, left: 40, bottom: 5 },
} as const;

/**
 * Default chart heights
 */
export const CHART_HEIGHTS = {
  default: 300,
  compact: 250,
  small: 200,
} as const;

/**
 * Shared CartesianGrid configuration
 */
export const CARTESIAN_GRID_PROPS = {
  strokeDasharray: '3 3',
  stroke: 'hsl(var(--muted-foreground) / 0.2)',
  vertical: false,
} as const;

/**
 * Shared axis tick styling
 */
export const AXIS_TICK_STYLE = {
  fill: 'hsl(var(--muted-foreground))',
  fontSize: 11,
} as const;

/**
 * Shared Tooltip content style
 */
export const TOOLTIP_CONTENT_STYLE = {
  backgroundColor: 'hsl(var(--popover))',
  border: '1px solid hsl(var(--border))',
  borderRadius: '8px',
  color: 'hsl(var(--popover-foreground))',
  fontSize: '12px',
} as const;

/**
 * Shared Legend configuration
 */
export const LEGEND_WRAPPER_STYLE = {
  fontSize: '12px',
};

export const LEGEND_ICON_SIZE = 10;

/**
 * Default bar size for consistency
 */
export const BAR_SIZE = 20;

/**
 * Default bar radius
 */
export const BAR_RADIUS: [number, number, number, number] = [4, 4, 0, 0];