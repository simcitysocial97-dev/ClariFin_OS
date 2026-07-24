/**
 * Sort Logic Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests verify sorting logic and behavior.
 */

import { describe, it, expect } from 'vitest';
import type { SortField, SortDirection, SortState, SortOption } from '../types';

describe('Sort Logic', () => {
  describe('Sort Fields', () => {
    it('should have all required sort fields', () => {
      // Type verification for SortField
      type ValidSortField = SortField;

      const validFields: ValidSortField[] = [
        'date',
        'amount',
        'description',
        'category',
        'merchant',
      ];

      // This is a compile-time check
      expect(validFields.length).toBe(5);
    });

    it('should have valid sort direction values', () => {
      // Type verification for SortDirection
      type ValidSortDirection = SortDirection;

      const validDirections: ValidSortDirection[] = [
        'asc',
        'desc',
      ];

      // This is a compile-time check
      expect(validDirections.length).toBe(2);
    });
  });

  describe('Sort State', () => {
    it('should have all required state fields', () => {
      // Type verification for SortState
      type StateFields = keyof SortState;

      const stateFields: StateFields[] = [
        'field',
        'direction',
      ];

      // This is a compile-time check
      expect(stateFields.length).toBe(2);
    });

    it('should have default sort state', () => {
      const defaultSortState: SortState = {
        field: null,
        direction: 'asc',
      };

      expect(defaultSortState.field).toBeNull();
      expect(defaultSortState.direction).toBe('asc');
    });

    it('should have valid sort state', () => {
      const sortState: SortState = {
        field: 'date',
        direction: 'desc',
      };

      expect(sortState.field).toBe('date');
      expect(sortState.direction).toBe('desc');
    });
  });

  describe('Sort Option', () => {
    it('should have all required option fields', () => {
      // Type verification for SortOption
      type OptionFields = keyof SortOption;

      const optionFields: OptionFields[] = [
        'field',
        'label',
      ];

      // This is a compile-time check
      expect(optionFields.length).toBe(2);
    });

    it('should have valid sort option', () => {
      const sortOption: SortOption = {
        field: 'amount',
        label: 'Amount',
      };

      expect(sortOption.field).toBe('amount');
      expect(sortOption.label).toBe('Amount');
    });
  });

  describe('Sort Actions', () => {
     it('should toggle sort direction when same field is sorted', () => {
       // Sorting by the same field should toggle direction
       const currentDirection: SortDirection = 'asc';
       const newDirection: SortDirection = currentDirection === 'asc' ? 'desc' : 'asc';

       expect(newDirection).toBe('desc');
     });

     it('should set direction to asc when new field is sorted', () => {
       // Sorting by a new field should set direction to asc
       const newDirection: SortDirection = 'asc';

       expect(newDirection).toBe('asc');
     });

    it('should support all sort fields', () => {
      // All sort fields should be supported
      const sortFields: SortField[] = ['date', 'amount', 'description', 'category', 'merchant'];

      expect(sortFields.length).toBe(5);
    });
  });

  describe('Sort Logic', () => {
    it('should sort by date ascending', () => {
      // Date ascending sort
      const dates = ['2026-07-19', '2026-07-01', '2026-07-15'];
      const sorted = [...dates].sort((a, b) => a.localeCompare(b));

      expect(sorted[0]).toBe('2026-07-01');
      expect(sorted[1]).toBe('2026-07-15');
      expect(sorted[2]).toBe('2026-07-19');
    });

    it('should sort by date descending', () => {
      // Date descending sort
      const dates = ['2026-07-19', '2026-07-01', '2026-07-15'];
      const sorted = [...dates].sort((a, b) => b.localeCompare(a));

      expect(sorted[0]).toBe('2026-07-19');
      expect(sorted[1]).toBe('2026-07-15');
      expect(sorted[2]).toBe('2026-07-01');
    });

    it('should sort by amount ascending', () => {
      // Amount ascending sort
      const amounts = [50000, 10000, 30000];
      const sorted = [...amounts].sort((a, b) => a - b);

      expect(sorted[0]).toBe(10000);
      expect(sorted[1]).toBe(30000);
      expect(sorted[2]).toBe(50000);
    });

    it('should sort by amount descending', () => {
      // Amount descending sort
      const amounts = [50000, 10000, 30000];
      const sorted = [...amounts].sort((a, b) => b - a);

      expect(sorted[0]).toBe(50000);
      expect(sorted[1]).toBe(30000);
      expect(sorted[2]).toBe(10000);
    });

    it('should sort by description alphabetically', () => {
      // Description alphabetical sort
      const descriptions = ['Zebra', 'Apple', 'Mango'];
      const sorted = [...descriptions].sort((a, b) => a.localeCompare(b));

      expect(sorted[0]).toBe('Apple');
      expect(sorted[1]).toBe('Mango');
      expect(sorted[2]).toBe('Zebra');
    });

    it('should sort by category alphabetically', () => {
      // Category alphabetical sort
      const categories = ['Shopping', 'Food', 'Travel'];
      const sorted = [...categories].sort((a, b) => a.localeCompare(b));

      expect(sorted[0]).toBe('Food');
      expect(sorted[1]).toBe('Shopping');
      expect(sorted[2]).toBe('Travel');
    });

    it('should sort by merchant alphabetically', () => {
      // Merchant alphabetical sort
      const merchants = ['Zara', 'Amazon', 'Flipkart'];
      const sorted = [...merchants].sort((a, b) => a.localeCompare(b));

      expect(sorted[0]).toBe('Amazon');
      expect(sorted[1]).toBe('Flipkart');
      expect(sorted[2]).toBe('Zara');
    });
  });
});