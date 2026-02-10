import { db } from '../db/database';
import { env } from '../config/env';
import { GuildSettings, RewardsMode } from '../types/domain';

export class GuildSettingsRepository {
  ensure(guildId: string): GuildSettings {
    const existing = db.prepare('SELECT * FROM guild_settings WHERE guild_id = ?').get(guildId) as GuildSettings | undefined;
    if (existing) return existing;
    db.prepare(`INSERT INTO guild_settings(guild_id, cooldown_seconds, rewards_mode, trinkets_enabled, quest_enabled, quest_deadline_hours)
      VALUES (?, ?, ?, ?, ?, ?)`)
      .run(guildId, env.defaultCooldownSeconds, env.defaultRewardsMode, env.defaultTrinketsEnabled ? 1 : 0, env.defaultQuestEnabled ? 1 : 0, env.defaultQuestDeadlineHours);
    return db.prepare('SELECT * FROM guild_settings WHERE guild_id = ?').get(guildId) as GuildSettings;
  }

  setCooldown(guildId: string, seconds: number): void {
    this.ensure(guildId);
    db.prepare('UPDATE guild_settings SET cooldown_seconds = ? WHERE guild_id = ?').run(seconds, guildId);
  }

  setRewardsMode(guildId: string, mode: RewardsMode): void {
    this.ensure(guildId);
    db.prepare('UPDATE guild_settings SET rewards_mode = ? WHERE guild_id = ?').run(mode, guildId);
  }

  setTrinketsEnabled(guildId: string, enabled: boolean): void {
    this.ensure(guildId);
    db.prepare('UPDATE guild_settings SET trinkets_enabled = ? WHERE guild_id = ?').run(enabled ? 1 : 0, guildId);
  }
}
