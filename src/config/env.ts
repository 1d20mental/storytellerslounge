import dotenv from 'dotenv';
import { RewardsMode } from '../types/domain';

dotenv.config();

function required(name: string, fallbackForTest?: string): string {
  const value = process.env[name];
  if (value) return value;
  if (process.env.NODE_ENV === 'test' && fallbackForTest) return fallbackForTest;
  throw new Error(`Missing required env var: ${name}`);
}

function parseBool(value: string | undefined, fallback: boolean): boolean {
  if (!value) return fallback;
  return ['true', '1', 'yes', 'on'].includes(value.toLowerCase());
}

function parseNumber(value: string | undefined, fallback: number): number {
  if (!value) return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parseRewardsMode(value: string | undefined, fallback: RewardsMode): RewardsMode {
  if (value === 'off' || value === 'flavor' || value === 'coins') return value;
  return fallback;
}

function parseWeights(raw: string | undefined): Record<string, number> {
  const defaults = { common: 60, uncommon: 25, rare: 10, epic: 4, legendary: 1 };
  if (!raw) return defaults;
  const pairs = raw.split(',').map((x) => x.trim()).filter(Boolean);
  const parsed: Record<string, number> = { ...defaults };
  for (const pair of pairs) {
    const [key, val] = pair.split(':');
    const n = Number(val);
    if (key && Number.isFinite(n) && n >= 0) parsed[key] = n;
  }
  return parsed;
}

export const env = {
  discordToken: required('DISCORD_TOKEN', 'test-token'),
  discordClientId: required('DISCORD_CLIENT_ID', 'test-client-id'),
  discordGuildId: process.env.DISCORD_GUILD_ID,
  databasePath: process.env.DATABASE_PATH ?? './data/bot.sqlite',
  defaultCooldownSeconds: parseNumber(process.env.DEFAULT_COOLDOWN_SECONDS, 45),
  defaultRewardsMode: parseRewardsMode(process.env.DEFAULT_REWARDS_MODE, 'coins'),
  defaultTrinketsEnabled: parseBool(process.env.DEFAULT_TRINKETS_ENABLED, true),
  defaultQuestEnabled: parseBool(process.env.DEFAULT_QUEST_ENABLED, true),
  defaultQuestDeadlineHours: parseNumber(process.env.DEFAULT_QUEST_DEADLINE_HOURS, 24),
  rarityWeights: parseWeights(process.env.RARITY_WEIGHTS),
  luckUpgradeChance: parseNumber(process.env.LUCK_UPGRADE_CHANCE, 0.04)
};
