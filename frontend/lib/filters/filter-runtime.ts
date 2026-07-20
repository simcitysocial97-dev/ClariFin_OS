/**
 * Filter Runtime - Stage 7.5 Runtime Consolidation
 *
 * Single filter engine for all workspaces.
 * Provides unified filtering with workspace-specific configuration.
 *
 * Architecture: FilterRuntime → Workspace Configuration → Existing Filter Implementations
 */

import type { DateFilter, AmountFilter } from './types';

// ===== Filter Configuration =====
export interface FilterConfig {
  workspace: string;
  dateFilter: DateFilter | null;
  amountFilter: AmountFilter | null;
  searchQuery: string;
  statusFilter: string[];
}

// ===== Filter Runtime =====
/**
 * Main runtime for filter management across all workspaces.
 * Provides unified filtering with workspace-specific configuration.
 */
export class FilterRuntime {
  private filters: Map<string, FilterConfig> = new Map();

  /**
   * Get filter configuration for a workspace
   */
  get(workspace: string): FilterConfig | undefined {
    return this.filters.get(workspace);
  }

  /**
   * Set filter configuration for a workspace
   */
  set(workspace: string, config: Partial<FilterConfig>): void {
    const existing = this.filters.get(workspace) || {
      workspace,
      dateFilter: null,
      amountFilter: null,
      searchQuery: '',
      statusFilter: [],
    };
    this.filters.set(workspace, { ...existing, ...config });
  }

  /**
   * Clear filters for a workspace
   */
  clear(workspace: string): void {
    this.filters.delete(workspace);
  }

  /**
   * Get all filter configurations
   */
  getAll(): FilterConfig[] {
    return Array.from(this.filters.values());
  }

  /**
   * Get all workspace names with active filters
   */
  getActiveWorkspaceNames(): string[] {
    return Array.from(this.filters.keys());
  }

  // ===== Date Filter =====
  setDateFilter(workspace: string, filter: DateFilter | null): void {
    this.set(workspace, { dateFilter: filter });
  }

  getDateFilter(workspace: string): DateFilter | null {
    return this.filters.get(workspace)?.dateFilter ?? null;
  }

  // ===== Amount Filter =====
  setAmountFilter(workspace: string, filter: AmountFilter | null): void {
    this.set(workspace, { amountFilter: filter });
  }

  getAmountFilter(workspace: string): AmountFilter | null {
    return this.filters.get(workspace)?.amountFilter ?? null;
  }

  // ===== Search Query =====
  setSearchQuery(workspace: string, query: string): void {
    this.set(workspace, { searchQuery: query });
  }

  getSearchQuery(workspace: string): string {
    return this.filters.get(workspace)?.searchQuery ?? '';
  }

  // ===== Status Filter =====
  setStatusFilter(workspace: string, statuses: string[]): void {
    this.set(workspace, { statusFilter: statuses });
  }

  getStatusFilter(workspace: string): string[] {
    return this.filters.get(workspace)?.statusFilter ?? [];
  }

  // ===== Active Filter Count =====
  getActiveFilterCount(workspace: string): number {
    const config = this.filters.get(workspace);
    if (!config) return 0;

    let count = 0;
    if (config.searchQuery) count++;
    if (config.dateFilter) count++;
    if (config.amountFilter) count++;
    if (config.statusFilter.length > 0) count++;
    return count;
  }

  // ===== Reset =====
  reset(): void {
    this.filters.clear();
  }
}

// ===== Convenience Export =====
export const filterRuntime = new FilterRuntime();