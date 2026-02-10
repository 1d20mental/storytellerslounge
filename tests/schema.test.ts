import { describe, expect, it } from 'vitest';
import { fishCatalogSchema } from '../src/utils/schema';

describe('fish catalog schema', () => {
  it('accepts valid entries and rejects malformed ones', () => {
    const valid = [{
      id: 'amur_catfish',
      name: 'Amur Catfish',
      water: 'fresh',
      rarity: 'rare',
      biomes: ['river'],
      weightRangeKg: [3, 7],
      lengthRangeCm: [40, 90],
      baseValue: 140,
      flavor: ['A whiskered heavyweight from murky waters.']
    }];
    expect(() => fishCatalogSchema.parse(valid)).not.toThrow();

    const invalid = [{ ...valid[0], weightRangeKg: [7, 3] }];
    expect(() => fishCatalogSchema.parse(invalid)).toThrow();
  });
});
