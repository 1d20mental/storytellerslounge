import fs from 'node:fs';
import path from 'node:path';
import { FishEntry, TrinketEntry, WaterType } from '../types/domain';
import { fishCatalogSchema, trinketCatalogSchema } from '../utils/schema';

export class CatalogService {
  fish: FishEntry[] = [];
  trinkets: TrinketEntry[] = [];

  load(fishPath = path.join(process.cwd(), 'data/fish.json'), trinketPath = path.join(process.cwd(), 'data/trinkets.json')): void {
    const fishRaw = JSON.parse(fs.readFileSync(fishPath, 'utf8'));
    const trinketRaw = JSON.parse(fs.readFileSync(trinketPath, 'utf8'));
    this.fish = fishCatalogSchema.parse(fishRaw);
    this.trinkets = trinketCatalogSchema.parse(trinketRaw);
  }

  getFishByWater(water: WaterType): FishEntry[] {
    return this.fish.filter((f) => f.water === water);
  }

  getFishById(id: string): FishEntry | undefined {
    return this.fish.find((f) => f.id === id);
  }
}
