import { describe, expect, it } from 'vitest';
import { rollWeightedRarity } from '../src/services/fishingService';

describe('rarity distribution', () => {
  it('roughly follows configured weights over many rolls', () => {
    const weights = { common: 60, uncommon: 25, rare: 10, epic: 4, legendary: 1 };
    const iterations = 100000;
    const counts: Record<string, number> = { common: 0, uncommon: 0, rare: 0, epic: 0, legendary: 0 };

    for (let i = 0; i < iterations; i++) {
      const rarity = rollWeightedRarity(weights);
      counts[rarity]++;
    }

    expect(counts.common / iterations).toBeGreaterThan(0.55);
    expect(counts.uncommon / iterations).toBeGreaterThan(0.2);
    expect(counts.rare / iterations).toBeGreaterThan(0.07);
    expect(counts.legendary / iterations).toBeLessThan(0.03);
  });
});
