import { z } from 'zod';

const raritySchema = z.enum(['common', 'uncommon', 'rare', 'epic', 'legendary']);

export const fishSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  water: z.enum(['fresh', 'salt']),
  rarity: raritySchema,
  biomes: z.array(z.string().min(1)).min(1),
  weightRangeKg: z.tuple([z.number().positive(), z.number().positive()]).refine(([min, max]) => max > min),
  lengthRangeCm: z.tuple([z.number().positive(), z.number().positive()]).refine(([min, max]) => max > min),
  baseValue: z.number().nonnegative(),
  flavor: z.array(z.string().min(1)).min(1)
});

export const fishCatalogSchema = z.array(fishSchema).min(1);

export const trinketSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  rarity: raritySchema,
  weight: z.number().positive(),
  flavor: z.string().min(1),
  baseValue: z.number().nonnegative().optional()
});

export const trinketCatalogSchema = z.array(trinketSchema).min(1);

export type FishCatalogInput = z.infer<typeof fishCatalogSchema>;
export type TrinketCatalogInput = z.infer<typeof trinketCatalogSchema>;
