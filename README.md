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

### 1. Get Your Rust+ Pairing Credentials

You need four values: **Server IP**, **Server Port**, **Steam64 ID**, and **Player Token**.

**Option A: RustPlus.py Link Companion (recommended)**

1. Install the [RustPlus.py Link Companion](https://chromewebstore.google.com/detail/rustpluspy-link-companion/gojhnmnggbnflhdcpcemeahejhcimnlf) Chrome extension
2. Open the extension and follow the instructions to link your Steam account
3. In Rust, open the Rust+ menu and click **Pair with Server**
4. The extension will display your server details and player token

**Option B: From the Rust+ app**

1. Install the Rust+ companion app on your phone
2. Pair with your server in-game (Tool Cupboard → Pair with Server)
3. Use a packet sniffer or the `rustplus.py` FCM listener to extract the credentials

### 2. Create a Discord Webhook

1. Open your Discord server
2. Go to **Server Settings → Integrations → Webhooks**
3. Click **New Webhook**
4. Choose a name (e.g. "Rust+ Alerts") and the target channel
5. Click **Copy Webhook URL**

### 3. Configure the Bot

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
RUST_SERVER_IP=123.456.789.0
RUST_SERVER_PORT=28015
RUST_PLAYER_ID=76561198000000000
RUST_PLAYER_TOKEN=your_token_here
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
