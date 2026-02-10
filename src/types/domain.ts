export type WaterType = 'fresh' | 'salt';
export type Rarity = 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
export type RewardsMode = 'off' | 'flavor' | 'coins';

export interface FishEntry {
  id: string;
  name: string;
  water: WaterType;
  rarity: Rarity;
  biomes: string[];
  weightRangeKg: [number, number];
  lengthRangeCm: [number, number];
  baseValue: number;
  flavor: string[];
}

export interface TrinketEntry {
  id: string;
  name: string;
  rarity: Rarity;
  weight: number;
  flavor: string;
  baseValue?: number;
}

export interface GuildSettings {
  guild_id: string;
  cooldown_seconds: number;
  rewards_mode: RewardsMode;
  trinkets_enabled: number;
  quest_enabled: number;
  quest_deadline_hours: number;
}
