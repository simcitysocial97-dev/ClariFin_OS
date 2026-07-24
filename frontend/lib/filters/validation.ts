/**
 * Filter Validation - Stage 3 Transaction Intelligence Workspace
 *
 * Validation utilities for transaction filters.
 */

import type { DateFilter, AmountFilter, TransactionFilters, FilterValidationResult } from './types';

/**
 * Validate date filter
 */
export function validateDateFilter(filter: DateFilter | null): FilterValidationResult {
  if (!filter) {
    return { valid: true };
  }

  if (filter.from && filter.to) {
    const fromDate = new Date(filter.from);
    const toDate = new Date(filter.to);

    if (isNaN(fromDate.getTime()) || isNaN(toDate.getTime())) {
      return { valid: false, error: 'Invalid date format' };
    }

    if (fromDate > toDate) {
      return { valid: false, error: 'From date must be before to date' };
    }
  }

  return { valid: true };
}

/**
 * Validate amount filter
 */
export function validateAmountFilter(filter: AmountFilter | null): FilterValidationResult {
  if (!filter) {
    return { valid: true };
  }

  if (filter.min !== undefined && filter.min < 0) {
    return { valid: false, error: 'Minimum amount cannot be negative' };
  }

  if (filter.max !== undefined && filter.max < 0) {
    return { valid: false, error: 'Maximum amount cannot be negative' };
  }

  if (filter.min !== undefined && filter.max !== undefined && filter.min > filter.max) {
    return { valid: false, error: 'Minimum amount must be less than maximum amount' };
  }

  return { valid: true };
}

/**
 * Validate all filters
 */
export function validateFilters(filters: TransactionFilters): FilterValidationResult[] {
  return [
    validateDateFilter(filters.dateFilter),
    validateAmountFilter(filters.amountFilter),
  ];
}

/**
 * Check if any filter is active
 */
export function hasActiveFilters(filters: TransactionFilters): boolean {
  return (
    filters.searchQuery.length > 0 ||
    filters.dateFilter !== null ||
    filters.categoryFilter.length > 0 ||
    filters.merchantFilter.length > 0 ||
    filters.amountFilter !== null ||
    filters.statusFilter.length > 0
  );
}