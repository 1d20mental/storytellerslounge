CREATE TABLE IF NOT EXISTS guild_settings (
  guild_id TEXT PRIMARY KEY,
  cooldown_seconds INTEGER NOT NULL DEFAULT 45,
  rewards_mode TEXT NOT NULL DEFAULT 'coins',
  trinkets_enabled INTEGER NOT NULL DEFAULT 1,
  quest_enabled INTEGER NOT NULL DEFAULT 1,
  quest_deadline_hours INTEGER NOT NULL DEFAULT 24
);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT NOT NULL,
  guild_id TEXT NOT NULL,
  coins INTEGER NOT NULL DEFAULT 0,
  last_fish_id INTEGER,
  last_caught_at TEXT,
  PRIMARY KEY (user_id, guild_id)
);

CREATE TABLE IF NOT EXISTS catches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guild_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  fish_id TEXT NOT NULL,
  water TEXT NOT NULL,
  rarity TEXT NOT NULL,
  weightKg REAL NOT NULL,
  lengthCm REAL NOT NULL,
  value INTEGER NOT NULL,
  caught_at TEXT NOT NULL DEFAULT (datetime('now')),
  sold_at TEXT
);

CREATE TABLE IF NOT EXISTS discovered_fish (
  guild_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  fish_id TEXT NOT NULL,
  first_caught_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (guild_id, user_id, fish_id)
);

CREATE TABLE IF NOT EXISTS trinkets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guild_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  trinket_text TEXT NOT NULL,
  value INTEGER NOT NULL DEFAULT 0,
  found_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cooldowns (
  guild_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  command_type TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  PRIMARY KEY (guild_id, user_id, command_type)
);

CREATE TABLE IF NOT EXISTS quests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guild_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  payout INTEGER NOT NULL,
  deadline_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  completed_at INTEGER
);

CREATE TABLE IF NOT EXISTS quest_targets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quest_id INTEGER NOT NULL,
  fish_id TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  FOREIGN KEY (quest_id) REFERENCES quests(id)
);
