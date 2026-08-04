import { describe, it, expect } from 'vitest';
import { cn } from '@/lib/utils';

describe('Utils Alias Test 2', () => {
  it('resolves @/lib/utils from interaction dir', () => {
    expect(cn).toBeDefined();
  });
});
