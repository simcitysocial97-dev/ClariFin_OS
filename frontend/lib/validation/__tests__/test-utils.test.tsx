import { describe, it, expect } from 'vitest';
import { cn } from '@/lib/utils';

describe('Utils Alias Test', () => {
  it('resolves @/lib/utils', () => {
    expect(cn).toBeDefined();
  });
});
