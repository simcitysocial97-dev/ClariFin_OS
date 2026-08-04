import { describe, it, expect } from 'vitest';
import { cn } from '@/lib/utils';

describe('Utils TS Alias Test', () => {
  it('resolves @/lib/utils from .ts file', () => {
    expect(cn).toBeDefined();
  });
});
