# Downtime Bot Repository Layout Contract

This project intentionally keeps downtime bot code and deployment assets isolated under `downtime_bot/`.

## Folder ownership
- `downtime_bot/` owns all bot-specific code, scripts, docs, and deploy files.
- Root-level bot files (`bot.py`, `src/`, etc.) belong to legacy/other bots and are not used by the downtime bot runtime.

## Required cross-project file (single exception)
The downtime bot reads the authoritative allowed-content JSON from:

`data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json`

This path is required by product requirements and remains outside `downtime_bot/` by design.

## Branch and merge expectation
Before deploying on a server, confirm the branch you are deploying includes `downtime_bot/`:

```bash
git ls-tree -d --name-only HEAD | rg '^downtime_bot$'
```

If this command prints nothing, that branch/revision is missing downtime bot files and must not be deployed.
