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
// All motion is semantic — no bounce, no elastic, no decorative scale.
export const motionClasses = {
  // Selection halo — 150ms semantic transition
  selectionHalo: 'transition-[box-shadow,opacity] duration-150 ease-out fin-node-halo',
  selectionPulse: 'fin-risk-pulse',

  // Hover — opacity/background only, never scale
  hoverScale: 'transition-colors duration-100 ease-out',

  // Focus effect
  focusRing: 'focus:outline-none fin-focus-ring',

  // Panel open — 120–180 ms
  panelOpen: 'transition-[opacity,transform] duration-150 ease-out',

  // Navigation — instant
  navigation: 'transition-none',

  // Smooth transition (non-scale properties only)
  smooth: 'transition-[opacity,background-color,border-color,box-shadow,color] duration-150 ease-out',
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