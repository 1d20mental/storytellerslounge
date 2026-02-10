# Discord Fishing Bot (Storytellers Lounge)

Production-ready Discord fishing minigame bot built with **TypeScript + discord.js v14 + SQLite (better-sqlite3)**.

## Features

- Slash commands for freshwater and saltwater fishing
- Data-driven fish catalog (`data/fish.json`) with rarity, biome, sizes, values, and flavor lines
- Weighted rarity rolls with optional luck-based rarity upgrade
- Optional trinket drops (`data/trinkets.json`) with weighted loot table
- Per-user, per-guild, per-command cooldowns
- Guild-level admin configuration for cooldown, rewards mode, trinkets, and fish import/export
- SQLite persistence with auto migrations
- Unit tests for rarity distribution, cooldown logic, and JSON schema validation
- Docker + docker-compose deployment support

## Commands

- `/fish` - Freshwater catch
- `/fishsea` - Saltwater catch
- `/fishdex [all]` - User discovered fish (or full catalog for admins)
- `/sell [catch_id]` - Sell last or selected catch (coins mode only)
- `/inventory` - Summary of fish count, trinkets, and coins
- `/quest` - Generates 3 random fish targets with payout + deadline
- `/admin setcooldown <seconds>`
- `/admin togglerewards <off|flavor|coins>`
- `/admin toggletrinkets <on|off>`
- `/admin importfish <attach JSON>`
- `/admin exportfish`

Admin commands require **Manage Server** permission.

## Project Structure

```
src/
  commands/
  config/
  db/
    migrations/
  i18n/
  repositories/
  services/
  types/
  utils/
package.json
tsconfig.json
.env.example
data/
  fish.json
  trinkets.json
Dockerfile
docker-compose.yml
```

## Setup (Local)

### 1) Create a Discord App + Bot
1. Open <https://discord.com/developers/applications>
2. Create **New Application**
3. In **Bot** tab, create/add bot user and copy token
4. In **OAuth2 > URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: at minimum `Send Messages`, `Use Slash Commands`
5. Invite bot to your server with generated URL

### 2) Configure environment
```bash
cp .env.example .env
# edit .env with your token/client id
```

### 3) Install and run migrations
```bash
npm install
npm run migrate
```

### 4) Register slash commands
```bash
npm run register:commands
```

Tip: set `DISCORD_GUILD_ID` for instant guild command updates during development.


### Discord Installation UI note (new developer portal)
If your **Install Link** still looks like `https://discord.com/oauth2/authorize?client_id=...`, that can be normal in Discord's new UI.
The link can stay short while Discord applies your **Default Install Settings** (Guild Install scopes + permissions) server-side.

For this bot, ensure **Guild Install** includes:
- Scopes: `bot`, `applications.commands`
- Permissions: `Send Messages`, `Use Slash Commands`

If needed, you can also use a fully explicit URL:

```
https://discord.com/oauth2/authorize?client_id=<YOUR_CLIENT_ID>&scope=bot%20applications.commands&permissions=2147485696
```


### 5) Run bot
```bash
npm run dev
```

Production:
```bash
npm run build
npm start
```

## Database

SQLite file path is configured by `DATABASE_PATH` (default `./data/bot.sqlite`).
Migrations live in `src/db/migrations` and are applied automatically at startup (and by `npm run migrate`).

## Fish JSON import format

Each entry must match:

```json
{
  "id": "unique_string",
  "name": "Amur Catfish",
  "water": "fresh",
  "rarity": "common",
  "biomes": ["river", "lake"],
  "weightRangeKg": [1.5, 8.2],
  "lengthRangeCm": [25, 90],
  "baseValue": 120,
  "flavor": ["line1", "line2"]
}
```

Invalid imports are rejected with actionable validation errors.

## Docker deployment

### Build and run with Docker Compose
```bash
docker compose up -d --build
```

### Logs
```bash
docker compose logs -f fishing-bot
```

## Tests

```bash
npm test
```

Includes:
- rarity roll distribution sanity test
- cooldown behavior test
- fish JSON schema validation test
