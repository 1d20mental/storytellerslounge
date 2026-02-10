import { db } from '../db/database';

export class CooldownRepository {
  getExpiry(guildId: string, userId: string, commandType: string): number | null {
    const row = db.prepare('SELECT expires_at FROM cooldowns WHERE guild_id = ? AND user_id = ? AND command_type = ?').get(guildId, userId, commandType) as { expires_at: number } | undefined;
    return row?.expires_at ?? null;
  }

  setExpiry(guildId: string, userId: string, commandType: string, expiryMs: number): void {
    db.prepare(`INSERT INTO cooldowns(guild_id, user_id, command_type, expires_at) VALUES (?, ?, ?, ?)
      ON CONFLICT(guild_id, user_id, command_type) DO UPDATE SET expires_at = excluded.expires_at`)
      .run(guildId, userId, commandType, expiryMs);
  }
}
