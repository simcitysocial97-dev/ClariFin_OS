import { describe, it, expect } from 'vitest';
import { keyboardEngine } from '@/lib/interaction/keyboard-engine';

describe('Alias Check', () => {
  it('resolves @/lib/interaction/keyboard-engine', () => {
    expect(keyboardEngine).toBeDefined();
  });
});
