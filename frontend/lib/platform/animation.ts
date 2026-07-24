/**
 * Animation Platform - Stage 8C Financial OS Visual System
 *
 * Cross-cutting animation utilities.
 */

import { motionClasses } from '../design-system/motion';

// ===== Animation Classes =====
export function getAnimationClass(animation: string): string {
  switch (animation) {
    case 'pulse':
      return 'fin-risk-pulse';
    case 'flow':
      return 'fin-edge-money-flow';
    case 'warning':
      // Risk uses subtle pulse — never bounce/elastic
      return 'fin-risk-pulse';
    case 'selection':
      return 'fin-node-halo';
    case 'simulation':
      return 'fin-simulation-pulse';
    default:
      return '';
  }
}

// ===== Transition Classes =====
export function getTransitionClass(): string {
  return motionClasses.smooth;
}

// ===== Stagger Delay =====
export function getStaggerDelay(index: number): string {
  return `${index * 50}ms`;
}