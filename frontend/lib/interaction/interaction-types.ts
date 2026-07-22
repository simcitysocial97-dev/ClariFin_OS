/**
 * Interaction Types - Stage 8F Financial OS Interaction Layer
 *
 * Core types for the interaction operating system.
 * These types are consumed by all workspaces.
 */

import type { WorkspaceName } from '../workspace';

// ===== Focus Types =====
export type FocusTarget =
  | 'panel'
  | 'widget'
  | 'graph'
  | 'table'
  | 'timeline'
  | 'inspector'
  | 'search';

export interface FocusState {
  currentTarget: FocusTarget | null;
  currentElementId: string | null;
  cycleIndex: number;
}

// ===== Keyboard Types =====
export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  cmd?: boolean;
  alt?: boolean;
  shift?: boolean;
  handler: (event: KeyboardEvent) => void;
  description: string;
  category: 'navigation' | 'selection' | 'workspace' | 'system' | 'search' | 'overlay' | 'graph';
}

export interface KeyboardHandler {
  shortcuts: KeyboardShortcut[];
  priority: number;
}

// ===== Command Types =====
export interface CommandMetadata {
  id: string;
  label: string;
  description?: string;
  category: 'workspace' | 'navigation' | 'search' | 'overlay' | 'system';
  icon?: string;
  shortcut?: string;
  workspace?: WorkspaceName;
  handler: () => void | Promise<void>;
  disabled?: () => boolean;
  hidden?: () => boolean;
  // Ranking support
  recent?: boolean;
  favorite?: boolean;
  alias?: string[];
}

// ===== Search Types =====
export type SearchResultType =
  | 'transaction'
  | 'account'
  | 'loan'
  | 'investment'
  | 'goal'
  | 'rule'
  | 'forecast'
  | 'merchant'
  | 'category'
  | 'tag'
  | 'insight'
  | 'command'
  | 'workspace';

export interface SearchResult {
  id: string;
  type: SearchResultType;
  label: string;
  description?: string;
  workspace?: WorkspaceName;
  value_paise?: number;
  metadata?: Record<string, unknown>;
}

// ===== Navigation Types =====
export interface NavigationEntry {
  id: string;
  label: string;
  workspace: WorkspaceName;
  entityId?: string;
  timestamp: number;
  pinned?: boolean;
}

// ===== Density Types =====
export type DensityMode = 'compact' | 'comfortable' | 'analytical';

export interface DensityConfig {
  mode: DensityMode;
  tableRowHeight: number;
  panelPadding: number;
  iconSize: number;
  fontSize: number;
}

// ===== Overlay Types =====
export type OverlayType =
  | 'money-flow'
  | 'risk'
  | 'confidence'
  | 'selection'
  | 'evidence'
  | 'simulation'
  | 'forecast'
  | 'dependencies'
  | 'ownership';

// ===== Selection Pipeline Types =====
export interface SelectionPipelineContext {
  nodeId: string | null;
  nodeType: string | null;
  workspace: WorkspaceName | null;
  timestamp: number;
}