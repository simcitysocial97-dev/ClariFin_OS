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
      return 'animate-pulse';
    case 'flow':
      return 'transition-all duration-300';
    case 'warning':
      return 'animate-bounce';
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