import { db } from '../db/database';
import { CatalogService } from './catalogService';

export class QuestService {
  constructor(private catalog: CatalogService) {}

  createQuest(guildId: string, userId: string, deadlineHours: number) {
    const fishPool = this.catalog.fish;
    const targets = Array.from({ length: 3 }).map(() => {
      const fish = fishPool[Math.floor(Math.random() * fishPool.length)];
      return { fishId: fish.id, quantity: Math.random() < 0.7 ? 1 : 2, fishName: fish.name };
    });

    const payout = targets.reduce((sum, t) => {
      const fish = this.catalog.getFishById(t.fishId)!;
      return sum + fish.baseValue * t.quantity;
    }, 0);

    const createdAt = Date.now();
    const deadlineAt = createdAt + deadlineHours * 60 * 60 * 1000;
    const result = db.prepare('INSERT INTO quests(guild_id, user_id, payout, deadline_at, created_at) VALUES (?, ?, ?, ?, ?)')
      .run(guildId, userId, payout, deadlineAt, createdAt);
    const questId = Number(result.lastInsertRowid);

    const stmt = db.prepare('INSERT INTO quest_targets(quest_id, fish_id, quantity) VALUES (?, ?, ?)');
    for (const target of targets) stmt.run(questId, target.fishId, target.quantity);

    return { payout, deadlineAt, targets };
  }
}
