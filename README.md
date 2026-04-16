# Rust+ Discord Notification Bot

Forwards Rust+ team events to a Discord channel — chat messages, smart alarms,
player online/offline, deaths, and server info.

## Features

- **Team chat** → plain text messages in Discord
- **Smart alarms / raids** → red embeds
- **Player deaths** → red embeds
- **Player online** → green embeds
- **Player offline** → gray embeds
- **Server info** → orange embeds (player count, map size)
- Auto-reconnect with exponential backoff
- Discord rate limit handling

## Requirements

- Python 3.10+
- A Rust server you're paired with via Rust+
- A Discord webhook URL

## Setup

### 1. Get Your FCM Credentials

You need FCM credentials to receive pairing notifications from Rust+.

**Step A: Register with FCM** (one-time setup, requires Node.js)

```bash
npx @liamcottle/rustplus.js fcm-register
```

This opens Chrome to log in with your Steam account. Once done, it saves your FCM credentials.

**Step B: Save credentials**

Copy the FCM output into a file called `fcm_credentials.json` in the project root.

### 2. Pair with Your Server

```bash
python pair.py
```

This starts listening for pairing notifications. Then in Rust:
1. Go to a **Tool Cupboard** or the **Rust+ menu**
2. Click **"Pair with Server"**

The script will capture the server IP, port, your player ID, and player token, and automatically write them to your `.env` file.

### 3. Create a Discord Webhook

1. Open your Discord server
2. Go to **Server Settings → Integrations → Webhooks**
3. Click **New Webhook**
4. Choose a name (e.g. "Rust+ Alerts") and the target channel
5. Click **Copy Webhook URL**
6. Add it to your `.env` file:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 4. Run with Docker Compose (Recommended)

```bash
docker compose up -d
```

That's it. The bot runs in the background and auto-restarts on failure.

**View logs:**
```bash
docker compose logs -f
```

**Stop:**
```bash
docker compose down
```

### 4b. Run without Docker (Alternative)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

## Event Examples

| Event | Discord Format |
|-------|---------------|
| Team chat | `**PlayerName:** hello team` |
| Player online | Green embed: "PlayerName is now online" |
| Player offline | Gray embed: "PlayerName went offline" |
| Player death | Red embed: "PlayerName has died" |
| Smart alarm | Red embed: "ALARM: Base Raid Alarm triggered" |
| Server info | Orange embed: server name, player count, map size |
