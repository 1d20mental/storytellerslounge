import { describe, expect, it } from 'vitest';
import { CooldownService } from '../src/services/cooldownService';

class FakeRepo {
  private map = new Map<string, number>();
  getExpiry(g: string, u: string, c: string) { return this.map.get(`${g}:${u}:${c}`) ?? null; }
  setExpiry(g: string, u: string, c: string, expiry: number) { this.map.set(`${g}:${u}:${c}`, expiry); }
}

describe('cooldown service', () => {
  it('blocks until expiry and returns remaining ms', () => {
    const repo = new FakeRepo();
    const service = new CooldownService(repo as any);

    const first = service.check('g1', 'u1', 'fresh', 30, 1000);
    expect(first.allowed).toBe(true);

    const second = service.check('g1', 'u1', 'fresh', 30, 2000);
    expect(second.allowed).toBe(false);
    expect(second.remainingMs).toBe(29000);

    const third = service.check('g1', 'u1', 'fresh', 30, 31001);
    expect(third.allowed).toBe(true);
  });
});
