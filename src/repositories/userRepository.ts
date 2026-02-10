import { db } from '../db/database';

export class UserRepository {
  ensure(userId: string, guildId: string): void {
    db.prepare('INSERT OR IGNORE INTO users(user_id, guild_id, coins) VALUES (?, ?, 0)').run(userId, guildId);
  }

  addCoins(userId: string, guildId: string, amount: number): void {
    this.ensure(userId, guildId);
    db.prepare('UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?').run(amount, userId, guildId);
  }

  getCoins(userId: string, guildId: string): number {
    this.ensure(userId, guildId);
    const row = db.prepare('SELECT coins FROM users WHERE user_id = ? AND guild_id = ?').get(userId, guildId) as { coins: number };
    return row.coins;
  }

  setLastFish(userId: string, guildId: string, catchId: number): void {
    this.ensure(userId, guildId);
    db.prepare("UPDATE users SET last_fish_id = ?, last_caught_at = datetime('now') WHERE user_id = ? AND guild_id = ?")
      .run(catchId, userId, guildId);
  }

  getLastFishId(userId: string, guildId: string): number | null {
    this.ensure(userId, guildId);
    const row = db.prepare('SELECT last_fish_id FROM users WHERE user_id = ? AND guild_id = ?').get(userId, guildId) as { last_fish_id: number | null };
    return row.last_fish_id;
  }
}
