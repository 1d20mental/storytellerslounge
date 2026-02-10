import { CooldownRepository } from '../repositories/cooldownRepository';

export class CooldownService {
  constructor(private repo: CooldownRepository) {}

  check(guildId: string, userId: string, commandType: string, cooldownSeconds: number, now = Date.now()) {
    const expires = this.repo.getExpiry(guildId, userId, commandType);
    if (expires && expires > now) {
      return { allowed: false, remainingMs: expires - now };
    }
    const nextExpiry = now + cooldownSeconds * 1000;
    this.repo.setExpiry(guildId, userId, commandType, nextExpiry);
    return { allowed: true, remainingMs: 0 };
  }
}
