/**
 * Design System Motion - Stage 8C Financial OS Visual System
 *
 * Animation system for financial meaning only.
 * No decorative effects.
 */

import { duration, easing } from './tokens';

// ===== Financial Motion =====
export const financialMotion = {
  // Money transfer - particle flow
  moneyTransfer: {
    duration: duration.normal,
    easing: easing.inOut,
    particleCount: 8,
    particleSize: 4,
  },

  // Selection - halo pulse
  selection: {
    duration: duration.fast,
    easing: easing.out,
    pulseScale: 1.2,
    pulseOpacity: 0.5,
  },

  // Risk - warning pulse
  risk: {
    duration: duration.slow,
    easing: easing.inOut,
    pulseScale: 1.1,
    pulseOpacity: 0.3,
  },

  // Simulation - dashed animated edge
  simulation: {
    dashArray: '5,5',
    dashOffset: 10,
    animationDuration: duration.slow,
  },

  // Confidence - opacity transition
  confidence: {
    high: { opacity: 1, transition: `${duration.fast} ${easing.out}` },
    medium: { opacity: 0.8, transition: `${duration.fast} ${easing.out}` },
    low: { opacity: 0.6, transition: `${duration.fast} ${easing.out}` },
  },

  // Focus - scale and border
  focus: {
    scale: 1.05,
    borderWidth: 2,
    transition: `${duration.fast} ${easing.out}`,
  },

  // Hover - subtle scale
  hover: {
    scale: 1.02,
    transition: `${duration.fast} ${easing.out}`,
  },
} as const;

// ===== CSS Animation Classes =====
export const motionClasses = {
  // Selection halo
  selectionHalo: 'transition-all duration-200 ease-out',
  selectionPulse: 'animate-pulse',

  // Hover effect
  hoverScale: 'transition-transform duration-150 ease-out hover:scale-105',

  // Focus effect
  focusRing: 'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',

  // Smooth transition
  smooth: 'transition-all duration-200 ease-in-out',
} as const;

// ===== Animation Keyframes =====
export const keyframes = {
  pulse: `
    0% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.1); }
    100% { opacity: 1; transform: scale(1); }
  `,

  dash: `
    from { stroke-dashoffset: 10; }
    to { stroke-dashoffset: 0; }
  `,
} as const;