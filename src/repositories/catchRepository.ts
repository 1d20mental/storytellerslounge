import { db } from '../db/database';

export interface CatchRecordInput {
  guildId: string;
  userId: string;
  fishId: string;
  water: string;
  rarity: string;
  weightKg: number;
  lengthCm: number;
  value: number;
}

export class CatchRepository {
  create(input: CatchRecordInput): number {
    const result = db.prepare(`INSERT INTO catches(guild_id, user_id, fish_id, water, rarity, weightKg, lengthCm, value)
      VALUES (@guildId, @userId, @fishId, @water, @rarity, @weightKg, @lengthCm, @value)`).run(input);
    return Number(result.lastInsertRowid);
  }

  discoverFish(guildId: string, userId: string, fishId: string): void {
    db.prepare('INSERT OR IGNORE INTO discovered_fish(guild_id, user_id, fish_id) VALUES (?, ?, ?)').run(guildId, userId, fishId);
  }

  getDiscoveredFish(guildId: string, userId: string): string[] {
    return db.prepare('SELECT fish_id FROM discovered_fish WHERE guild_id = ? AND user_id = ? ORDER BY fish_id').all(guildId, userId).map((r: any) => r.fish_id as string);
  }

  getCatchById(id: number) {
    return db.prepare('SELECT * FROM catches WHERE id = ?').get(id) as any;
  }

  sellCatch(id: number): boolean {
    const result = db.prepare("UPDATE catches SET sold_at = datetime('now') WHERE id = ? AND sold_at IS NULL").run(id);
    return result.changes > 0;
  }

  countUserCatches(guildId: string, userId: string): number {
    const row = db.prepare('SELECT COUNT(*) as count FROM catches WHERE guild_id = ? AND user_id = ?').get(guildId, userId) as { count: number };
    return row.count;
  }

  listUserTrinkets(guildId: string, userId: string): { trinket_text: string; value: number }[] {
    return db.prepare('SELECT trinket_text, value FROM trinkets WHERE guild_id = ? AND user_id = ? ORDER BY found_at DESC').all(guildId, userId) as any;
  }

  addTrinket(guildId: string, userId: string, text: string, value: number): void {
    db.prepare('INSERT INTO trinkets(guild_id, user_id, trinket_text, value) VALUES (?, ?, ?, ?)').run(guildId, userId, text, value);
  }
}
