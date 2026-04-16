# Rust+ Discord Notification Bot — Design Spec

## Overview

A Python bot that connects to a Rust game server via the Rust+ companion API (as a regular player, not admin) and forwards all team events to a single Discord channel using webhooks. Runs 24/7 on a VPS.

## Goals

- Forward team-visible Rust+ events to Discord in real-time
- Rich embeds for critical events, plain text for routine events
- Simple setup with clear instructions for obtaining Rust+ pairing credentials
- Reliable 24/7 operation with auto-reconnect

## Non-Goals

- No RCON or admin-level access (player-only)
- No Discord bot commands or interactivity (webhook-only, one-way)
- No multi-server support (single server at a time)
- No database or persistent storage

## Architecture

Single async Python process with three layers:

```
┌─────────────────────────────────────────┐
│              main.py (entry)            │
│         asyncio event loop              │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌────────────────┐  │
│  │  rust_plus   │───>│   formatter    │  │
│  │  listener    │    │   (events →    │  │
│  │              │    │    payloads)   │  │
│  └─────────────┘    └───────┬────────┘  │
│                             │           │
│                     ┌───────▼────────┐  │
│                     │   discord      │  │
│                     │   sender       │  │
│                     │   (webhook)    │  │
│                     └────────────────┘  │
│                                         │
├─────────────────────────────────────────┤
│              config.py                  │
│         (.env file loader)              │
└─────────────────────────────────────────┘
```

### Components

**`main.py`** — Entry point. Loads config, initializes the Rust+ connection, registers event handlers, runs the async loop. Handles graceful shutdown and auto-reconnect on disconnect.

**`rust_listener.py`** — Connects to the Rust+ API via `rustplus.py`. Registers callbacks for:
- Team chat messages
- Smart alarm notifications
- Team member online/offline changes
- Team member deaths
- Server info polling (player count, wipe schedule, map size)

Passes raw event data to the formatter.

**`formatter.py`** — Transforms raw Rust+ events into Discord webhook payloads:
- **Rich embeds** for critical events:
  - Smart alarms / raid alerts → Red embed (`#FF4444`)
  - Player deaths → Red embed (`#FF4444`)
  - Server wipe / server info → Orange embed (`#FF8C00`)
  - Player online → Green embed (`#44FF44`)
  - Player offline → Gray embed (`#808080`)
- **Plain text** for routine events:
  - Team chat messages → Simple text with player name prefix

Each payload includes a timestamp.

**`discord_sender.py`** — Posts formatted payloads to the Discord webhook URL. Handles:
- Rate limiting (Discord webhook rate limits: 30 requests/60 seconds per channel)
- Retry with backoff on transient failures
- Message queue to batch rapid events

**`config.py`** — Loads configuration from a `.env` file:
- `RUST_SERVER_IP` — Server IP address
- `RUST_SERVER_PORT` — Rust+ companion port
- `RUST_PLAYER_ID` — Your Steam64 ID
- `RUST_PLAYER_TOKEN` — Rust+ player token (from pairing)
- `DISCORD_WEBHOOK_URL` — Discord channel webhook URL

## Event Details

### Team Chat Messages
- **Source:** `rustplus.py` team chat event listener
- **Format:** Plain text: `**PlayerName:** message content`
- **Frequency:** As they happen

### Smart Alarms
- **Source:** `rustplus.py` smart alarm notifications
- **Format:** Red embed with alarm name and "TRIGGERED" status
- **Frequency:** On trigger

### Player Online/Offline
- **Source:** Polling team info at regular intervals (every 30 seconds)
- **Format:** Green embed (online) / Gray embed (offline) with player name
- **Frequency:** On state change (track previous state to avoid duplicates)

### Player Deaths
- **Source:** Team chat event or team info changes
- **Format:** Red embed with player name and death message
- **Frequency:** As they happen

### Server Info
- **Source:** Polling server info at regular intervals (every 5 minutes)
- **Format:** Orange embed with player count, map size, wipe info
- **Frequency:** On significant changes or periodic summary

## Reconnection Strategy

1. On disconnect, wait 5 seconds and retry
2. Exponential backoff: 5s → 10s → 20s → 40s → max 60s
3. Log all reconnection attempts
4. Reset backoff on successful reconnect
5. Send a Discord notification on disconnect and reconnect

## File Structure

```
rust/
├── .env.example          # Template config with placeholder values
├── .env                  # Actual config (gitignored)
├── .gitignore
├── requirements.txt      # rustplus.py, aiohttp, python-dotenv
├── README.md             # Setup guide with pairing instructions
├── src/
│   ├── __init__.py
│   ├── main.py           # Entry point, async loop, reconnect logic
│   ├── config.py         # .env loader and validation
│   ├── rust_listener.py  # Rust+ API connection and event handlers
│   ├── formatter.py      # Event → Discord payload formatting
│   └── discord_sender.py # Webhook posting with rate limiting
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-16-rustplus-discord-bot-design.md
```

## Dependencies

- **Python 3.10+**
- **`rustplus.py`** — Rust+ companion API client
- **`aiohttp`** — Async HTTP for webhook posting
- **`python-dotenv`** — Load `.env` config

## Setup Guide (included in README)

### Getting Rust+ Pairing Credentials

1. Install the **Rust+** companion app on your phone (iOS/Android)
2. In-game, go to a **Tool Cupboard** or the **main menu Rust+ section**
3. Click **"Pair with Server"** — this links your Steam account
4. Use the `rustplus.py` pairing utility or the **RustPlus.py Link Companion** browser extension to extract:
   - Server IP and port
   - Your Steam64 ID
   - Your player token
5. Enter these values in the `.env` file

### Creating a Discord Webhook

1. In Discord, go to **Server Settings → Integrations → Webhooks**
2. Click **New Webhook**
3. Name it (e.g., "Rust+ Alerts"), choose the target channel
4. Copy the webhook URL
5. Paste it into the `.env` file

## Error Handling

- **Rust+ connection lost:** Auto-reconnect with backoff, notify Discord
- **Discord webhook fails:** Retry with backoff, log errors, queue messages
- **Invalid config:** Fail fast on startup with clear error message
- **Rate limited by Discord:** Respect `Retry-After` header, queue messages

## Testing Strategy

- Unit tests for `formatter.py` (event → payload mapping)
- Unit tests for `config.py` (validation, missing values)
- Integration test with mock Rust+ events → verify Discord payloads
- Manual end-to-end test with a real server
