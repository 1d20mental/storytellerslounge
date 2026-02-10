import { env } from '../config/env';
import { CatchRepository } from '../repositories/catchRepository';
import { UserRepository } from '../repositories/userRepository';
import { CatalogService } from './catalogService';
import { Rarity, RewardsMode, WaterType } from '../types/domain';

const rarityOrder: Rarity[] = ['common', 'uncommon', 'rare', 'epic', 'legendary'];

export function rollWeightedRarity(weights: Record<string, number>, random = Math.random): Rarity {
  const total = rarityOrder.reduce((sum, r) => sum + (weights[r] ?? 0), 0);
  const roll = random() * total;
  let cursor = 0;
  for (const rarity of rarityOrder) {
    cursor += weights[rarity] ?? 0;
    if (roll <= cursor) return rarity;
  }
  return 'common';
}

function maybeUpgradeRarity(rarity: Rarity, chance: number, random = Math.random): Rarity {
  if (random() > chance) return rarity;
  const idx = rarityOrder.indexOf(rarity);
  return rarityOrder[Math.min(rarityOrder.length - 1, idx + 1)];
}

function rollRange([min, max]: [number, number], random = Math.random): number {
  return min + random() * (max - min);
}

export class FishingService {
  constructor(private catalog: CatalogService, private catches: CatchRepository, private users: UserRepository) {}

  fish(guildId: string, userId: string, water: WaterType, rewardsMode: RewardsMode, trinketsEnabled: boolean) {
    const waterPool = this.catalog.getFishByWater(water);
    let rarity = maybeUpgradeRarity(rollWeightedRarity(env.rarityWeights), env.luckUpgradeChance);
    const rarityPool = waterPool.filter((f) => f.rarity === rarity);
    if (rarityPool.length === 0) {
      rarity = 'common';
    }
    const pool = waterPool.filter((f) => f.rarity === rarity);
    const fish = pool[Math.floor(Math.random() * pool.length)] ?? waterPool[Math.floor(Math.random() * waterPool.length)];

    const weight = Number(rollRange(fish.weightRangeKg).toFixed(2));
    const length = Number(rollRange(fish.lengthRangeCm).toFixed(1));
    const midpointWeight = (fish.weightRangeKg[0] + fish.weightRangeKg[1]) / 2;
    const value = Math.max(1, Math.round(fish.baseValue * (weight / midpointWeight)));
    const persistedValue = rewardsMode === 'coins' ? value : 0;

    const catchId = this.catches.create({
      guildId,
      userId,
      fishId: fish.id,
      water,
      rarity: fish.rarity,
      weightKg: weight,
      lengthCm: length,
      value: persistedValue
    });
    this.catches.discoverFish(guildId, userId, fish.id);
    this.users.setLastFish(userId, guildId, catchId);

    let trinket: { name: string; flavor: string; value: number } | null = null;
    if (trinketsEnabled && this.catalog.trinkets.length > 0 && Math.random() < 0.2) {
      const totalWeight = this.catalog.trinkets.reduce((sum, t) => sum + t.weight, 0);
      let roll = Math.random() * totalWeight;
      for (const candidate of this.catalog.trinkets) {
        roll -= candidate.weight;
        if (roll <= 0) {
          trinket = {
            name: candidate.name,
            flavor: candidate.flavor,
            value: rewardsMode === 'coins' ? candidate.baseValue ?? 0 : 0
          };
          this.catches.addTrinket(guildId, userId, `${candidate.name}: ${candidate.flavor}`, trinket.value);
          if (trinket.value > 0) this.users.addCoins(userId, guildId, trinket.value);
          break;
        }
      }
    }

    if (rewardsMode === 'coins') this.users.addCoins(userId, guildId, persistedValue);

    return { fish, weight, length, value: persistedValue, trinket };
  }
}
