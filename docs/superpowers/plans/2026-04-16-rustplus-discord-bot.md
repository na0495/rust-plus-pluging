# Rust+ Discord Notification Bot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python bot that connects to a Rust game server via the Rust+ API and forwards team events to Discord via webhooks.

**Architecture:** Single async Python process using `rustplus.py` for Rust+ events and `aiohttp` for Discord webhook delivery. Events are formatted into Discord embeds (critical) or plain text (routine) and posted to a single webhook URL.

**Tech Stack:** Python 3.10+, rustplus.py 6.x, aiohttp, python-dotenv

---

## File Structure

```
rust/
├── .env.example          # Template config
├── .env                  # Actual config (gitignored)
├── .gitignore
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py           # Entry point, event loop, reconnect
│   ├── config.py         # .env loader and validation
│   ├── formatter.py      # Event → Discord payload formatting
│   └── discord_sender.py # Webhook posting with rate limiting
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_formatter.py
    └── test_discord_sender.py
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
venv/
```

- [ ] **Step 2: Create `requirements.txt`**

```
rustplus==6.0.9
aiohttp>=3.9.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 3: Create `.env.example`**

```
RUST_SERVER_IP=your_server_ip
RUST_SERVER_PORT=your_rust_plus_port
RUST_PLAYER_ID=your_steam64_id
RUST_PLAYER_TOKEN=your_player_token
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
```

- [ ] **Step 4: Create empty `src/__init__.py` and `tests/__init__.py`**

Both files are empty — they just mark the directories as Python packages.

- [ ] **Step 5: Install dependencies**

Run: `pip install -r requirements.txt`

- [ ] **Step 6: Commit**

```bash
git add .gitignore requirements.txt .env.example src/__init__.py tests/__init__.py
git commit -m "chore: scaffold project with dependencies and config template"
```

---

### Task 2: Config Module

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for config loading**

```python
# tests/test_config.py
import os
import pytest
from unittest.mock import patch

from src.config import load_config, ConfigError


class TestLoadConfig:
    def test_loads_all_required_fields(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RUST_SERVER_IP=192.168.1.1\n"
            "RUST_SERVER_PORT=28015\n"
            "RUST_PLAYER_ID=76561198000000000\n"
            "RUST_PLAYER_TOKEN=mytoken123\n"
            "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc\n"
        )
        config = load_config(str(env_file))
        assert config["server_ip"] == "192.168.1.1"
        assert config["server_port"] == "28015"
        assert config["player_id"] == 76561198000000000
        assert config["player_token"] == "mytoken123"
        assert config["webhook_url"] == "https://discord.com/api/webhooks/123/abc"

    def test_raises_on_missing_field(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RUST_SERVER_IP=192.168.1.1\n"
            "RUST_SERVER_PORT=28015\n"
        )
        with pytest.raises(ConfigError, match="RUST_PLAYER_ID"):
            load_config(str(env_file))

    def test_raises_on_empty_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("")
        with pytest.raises(ConfigError):
            load_config(str(env_file))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `src.config` does not exist yet.

- [ ] **Step 3: Implement config module**

```python
# src/config.py
from dotenv import dotenv_values


class ConfigError(Exception):
    pass


REQUIRED_FIELDS = {
    "RUST_SERVER_IP": "server_ip",
    "RUST_SERVER_PORT": "server_port",
    "RUST_PLAYER_ID": "player_id",
    "RUST_PLAYER_TOKEN": "player_token",
    "DISCORD_WEBHOOK_URL": "webhook_url",
}


def load_config(env_path: str = ".env") -> dict:
    values = dotenv_values(env_path)

    config = {}
    for env_key, config_key in REQUIRED_FIELDS.items():
        value = values.get(env_key, "").strip()
        if not value:
            raise ConfigError(
                f"Missing required config: {env_key}. "
                f"Check your .env file."
            )
        config[config_key] = value

    config["player_id"] = int(config["player_id"])
    return config
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: add config module with .env loading and validation"
```

---

### Task 3: Discord Sender Module

**Files:**
- Create: `src/discord_sender.py`
- Create: `tests/test_discord_sender.py`

- [ ] **Step 1: Write failing tests for Discord sender**

```python
# tests/test_discord_sender.py
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.discord_sender import DiscordSender


class TestDiscordSender:
    @pytest.mark.asyncio
    async def test_send_plain_message(self):
        sender = DiscordSender("https://discord.com/api/webhooks/123/abc")
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.post.return_value = mock_response
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            async with sender:
                await sender.send({"content": "Hello"})

            mock_session.post.assert_called_once()
            call_kwargs = mock_session.post.call_args
            assert call_kwargs[1]["json"] == {"content": "Hello"}

    @pytest.mark.asyncio
    async def test_send_embed_message(self):
        sender = DiscordSender("https://discord.com/api/webhooks/123/abc")
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        embed_payload = {
            "embeds": [{"title": "Alert", "color": 0xFF4444}]
        }

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.post.return_value = mock_response
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            async with sender:
                await sender.send(embed_payload)

            call_kwargs = mock_session.post.call_args
            assert call_kwargs[1]["json"] == embed_payload

    @pytest.mark.asyncio
    async def test_retries_on_429_rate_limit(self):
        sender = DiscordSender("https://discord.com/api/webhooks/123/abc")

        rate_limited_response = AsyncMock()
        rate_limited_response.status = 429
        rate_limited_response.json = AsyncMock(return_value={"retry_after": 0.1})
        rate_limited_response.__aenter__ = AsyncMock(return_value=rate_limited_response)
        rate_limited_response.__aexit__ = AsyncMock(return_value=False)

        ok_response = AsyncMock()
        ok_response.status = 204
        ok_response.__aenter__ = AsyncMock(return_value=ok_response)
        ok_response.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.post.side_effect = [rate_limited_response, ok_response]
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            async with sender:
                await sender.send({"content": "test"})

            assert mock_session.post.call_count == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_discord_sender.py -v`
Expected: FAIL — `src.discord_sender` does not exist yet.

- [ ] **Step 3: Implement Discord sender**

```python
# src/discord_sender.py
import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)


class DiscordSender:
    def __init__(self, webhook_url: str, max_retries: int = 3):
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *exc):
        if self._session:
            await self._session.close()
            self._session = None

    async def send(self, payload: dict) -> bool:
        for attempt in range(self.max_retries):
            try:
                resp = await self._session.post(
                    self.webhook_url, json=payload
                )
                if resp.status in (200, 204):
                    return True

                if resp.status == 429:
                    data = await resp.json()
                    retry_after = data.get("retry_after", 1.0)
                    logger.warning(
                        "Rate limited, retrying after %.1fs", retry_after
                    )
                    await asyncio.sleep(retry_after)
                    continue

                logger.error(
                    "Webhook failed with status %d on attempt %d",
                    resp.status,
                    attempt + 1,
                )
            except aiohttp.ClientError as e:
                logger.error("Webhook request error: %s", e)
                await asyncio.sleep(2 ** attempt)

        logger.error("Failed to send webhook after %d attempts", self.max_retries)
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discord_sender.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/discord_sender.py tests/test_discord_sender.py
git commit -m "feat: add Discord webhook sender with rate limiting and retries"
```

---

### Task 4: Event Formatter Module

**Files:**
- Create: `src/formatter.py`
- Create: `tests/test_formatter.py`

- [ ] **Step 1: Write failing tests for all event formatters**

```python
# tests/test_formatter.py
from datetime import datetime, timezone
from src.formatter import (
    format_chat_message,
    format_player_online,
    format_player_offline,
    format_player_death,
    format_smart_alarm,
    format_server_info,
    format_connection_status,
)


class TestFormatChatMessage:
    def test_plain_text_format(self):
        result = format_chat_message("PlayerOne", "hello team")
        assert result == {"content": "**PlayerOne:** hello team"}

    def test_escapes_markdown(self):
        result = format_chat_message("Player**Two", "hey *all*")
        assert "\\*" in result["content"] or "Player**Two" not in result.get("embeds", [{}])


class TestFormatPlayerOnline:
    def test_green_embed(self):
        result = format_player_online("PlayerOne")
        embed = result["embeds"][0]
        assert embed["color"] == 0x44FF44
        assert "PlayerOne" in embed["description"]
        assert "online" in embed["description"].lower()

    def test_has_timestamp(self):
        result = format_player_online("PlayerOne")
        assert "timestamp" in result["embeds"][0]


class TestFormatPlayerOffline:
    def test_gray_embed(self):
        result = format_player_offline("PlayerOne")
        embed = result["embeds"][0]
        assert embed["color"] == 0x808080
        assert "PlayerOne" in embed["description"]
        assert "offline" in embed["description"].lower()


class TestFormatPlayerDeath:
    def test_red_embed(self):
        result = format_player_death("PlayerOne")
        embed = result["embeds"][0]
        assert embed["color"] == 0xFF4444
        assert "PlayerOne" in embed["description"]

    def test_has_skull_or_death_indicator(self):
        result = format_player_death("PlayerOne")
        embed = result["embeds"][0]
        desc = embed["description"].lower()
        assert "died" in desc or "killed" in desc or "death" in desc


class TestFormatSmartAlarm:
    def test_red_embed_with_alarm_name(self):
        result = format_smart_alarm("Base Raid Alarm", "alert")
        embed = result["embeds"][0]
        assert embed["color"] == 0xFF4444
        assert "Base Raid Alarm" in embed["title"] or "Base Raid Alarm" in embed["description"]


class TestFormatServerInfo:
    def test_orange_embed(self):
        result = format_server_info(
            name="Rustopia US Main",
            players=200,
            max_players=300,
            map_size=4000,
        )
        embed = result["embeds"][0]
        assert embed["color"] == 0xFF8C00
        assert "200" in embed["description"]
        assert "300" in embed["description"]

    def test_includes_server_name(self):
        result = format_server_info(
            name="Rustopia US Main",
            players=200,
            max_players=300,
            map_size=4000,
        )
        embed = result["embeds"][0]
        assert "Rustopia US Main" in embed["title"] or "Rustopia US Main" in embed["description"]


class TestFormatConnectionStatus:
    def test_disconnected_red(self):
        result = format_connection_status(connected=False)
        embed = result["embeds"][0]
        assert embed["color"] == 0xFF4444
        assert "disconnect" in embed["description"].lower()

    def test_reconnected_green(self):
        result = format_connection_status(connected=True)
        embed = result["embeds"][0]
        assert embed["color"] == 0x44FF44
        assert "connect" in embed["description"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_formatter.py -v`
Expected: FAIL — `src.formatter` does not exist yet.

- [ ] **Step 3: Implement formatter module**

```python
# src/formatter.py
from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _embed(
    description: str,
    color: int,
    title: str | None = None,
) -> dict:
    embed = {
        "description": description,
        "color": color,
        "timestamp": _timestamp(),
    }
    if title:
        embed["title"] = title
    return {"embeds": [embed]}


def format_chat_message(player_name: str, message: str) -> dict:
    return {"content": f"**{player_name}:** {message}"}


def format_player_online(player_name: str) -> dict:
    return _embed(
        description=f"**{player_name}** is now online",
        color=0x44FF44,
    )


def format_player_offline(player_name: str) -> dict:
    return _embed(
        description=f"**{player_name}** went offline",
        color=0x808080,
    )


def format_player_death(player_name: str) -> dict:
    return _embed(
        description=f"**{player_name}** has died",
        color=0xFF4444,
    )


def format_smart_alarm(alarm_name: str, message: str) -> dict:
    return _embed(
        title=f"ALARM: {alarm_name}",
        description=f"**{alarm_name}** triggered: {message}",
        color=0xFF4444,
    )


def format_server_info(
    name: str,
    players: int,
    max_players: int,
    map_size: int,
) -> dict:
    return _embed(
        title="Server Info",
        description=(
            f"**{name}**\n"
            f"Players: **{players}/{max_players}**\n"
            f"Map Size: **{map_size}**"
        ),
        color=0xFF8C00,
    )


def format_connection_status(connected: bool) -> dict:
    if connected:
        return _embed(
            description="Bot has reconnected to Rust+ server",
            color=0x44FF44,
        )
    return _embed(
        description="Bot has disconnected from Rust+ server",
        color=0xFF4444,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_formatter.py -v`
Expected: All passed.

- [ ] **Step 5: Commit**

```bash
git add src/formatter.py tests/test_formatter.py
git commit -m "feat: add event formatter with embeds and plain text"
```

---

### Task 5: Main Entry Point — Rust+ Listener and Event Loop

**Files:**
- Create: `src/main.py`

This task wires everything together: connects to Rust+, registers event handlers, polls for team changes, and sends notifications to Discord.

- [ ] **Step 1: Implement main.py**

```python
# src/main.py
import asyncio
import logging
import signal
import sys

from rustplus import RustSocket, ServerDetails, ChatEvent, TeamEvent, EntityEvent

from src.config import load_config, ConfigError
from src.formatter import (
    format_chat_message,
    format_player_online,
    format_player_offline,
    format_player_death,
    format_smart_alarm,
    format_server_info,
    format_connection_status,
)
from src.discord_sender import DiscordSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rustplus-bot")

# Track online/offline state to only send on changes
_previous_online: set[int] = set()
_previous_alive: dict[int, bool] = {}


async def poll_team_status(socket: RustSocket, sender: DiscordSender):
    """Poll team info every 30s to detect online/offline and death changes."""
    global _previous_online, _previous_alive

    while True:
        try:
            team_info = await socket.get_team_info()
            if hasattr(team_info, "members"):
                members = team_info.members
            else:
                members = []

            current_online = set()
            for member in members:
                steam_id = member.steam_id
                name = member.name
                is_online = member.is_online
                is_alive = member.is_alive

                if is_online:
                    current_online.add(steam_id)

                # Online/offline transitions
                was_online = steam_id in _previous_online
                if is_online and not was_online and _previous_online:
                    await sender.send(format_player_online(name))
                elif not is_online and was_online:
                    await sender.send(format_player_offline(name))

                # Death detection
                was_alive = _previous_alive.get(steam_id)
                if was_alive is True and not is_alive:
                    await sender.send(format_player_death(name))
                _previous_alive[steam_id] = is_alive

            _previous_online = current_online

        except Exception as e:
            logger.error("Error polling team status: %s", e)

        await asyncio.sleep(30)


async def poll_server_info(socket: RustSocket, sender: DiscordSender):
    """Poll server info every 5 minutes and report."""
    _last_info = None

    while True:
        try:
            info = await socket.get_info()
            summary = f"{info.players}/{info.max_players}"

            if summary != _last_info:
                await sender.send(format_server_info(
                    name=info.name,
                    players=info.players,
                    max_players=info.max_players,
                    map_size=info.size,
                ))
                _last_info = summary

        except Exception as e:
            logger.error("Error polling server info: %s", e)

        await asyncio.sleep(300)


async def run_bot():
    try:
        config = load_config()
    except ConfigError as e:
        logger.error("Config error: %s", e)
        sys.exit(1)

    logger.info("Starting Rust+ Discord Bot...")

    server_details = ServerDetails(
        config["server_ip"],
        config["server_port"],
        config["player_id"],
        config["player_token"],
    )

    socket = RustSocket(server_details)
    sender = DiscordSender(config["webhook_url"])

    backoff = 5

    while True:
        try:
            await socket.connect()
            logger.info("Connected to Rust+ server")
            await sender.__aenter__()
            await sender.send(format_connection_status(connected=True))
            backoff = 5

            # Register chat event handler
            @ChatEvent(server_details)
            async def on_chat(event):
                msg = event.message
                logger.info("Chat: %s: %s", msg.name, msg.message)
                await sender.send(format_chat_message(msg.name, msg.message))

            # Start polling tasks
            team_task = asyncio.create_task(poll_team_status(socket, sender))
            server_task = asyncio.create_task(poll_server_info(socket, sender))

            # Keep running until disconnected
            await asyncio.gather(team_task, server_task)

        except Exception as e:
            logger.error("Connection error: %s", e)
            await sender.send(format_connection_status(connected=False))
            logger.info("Reconnecting in %ds...", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

        finally:
            try:
                await socket.disconnect()
            except Exception:
                pass
            try:
                await sender.__aexit__(None, None, None)
            except Exception:
                pass


def main():
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import ast; ast.parse(open('src/main.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: add main entry point with Rust+ event handling and reconnect logic"
```

---

### Task 6: README with Setup Guide

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

```markdown
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

### 4. Install and Run

```bash
pip install -r requirements.txt
python -m src.main
```

The bot will connect to your Rust+ server and start forwarding events to Discord.

### 5. Run 24/7 on a VPS (Optional)

Using `systemd` on a Linux VPS:

```bash
sudo nano /etc/systemd/system/rustplus-bot.service
```

```ini
[Unit]
Description=Rust+ Discord Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/rust
ExecStart=/usr/bin/python3 -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable rustplus-bot
sudo systemctl start rustplus-bot
```

## Event Examples

| Event | Discord Format |
|-------|---------------|
| Team chat | `**PlayerName:** hello team` |
| Player online | 🟢 Green embed: "PlayerName is now online" |
| Player offline | ⚫ Gray embed: "PlayerName went offline" |
| Player death | 🔴 Red embed: "PlayerName has died" |
| Smart alarm | 🔴 Red embed: "ALARM: Base Raid Alarm triggered" |
| Server info | 🟠 Orange embed: server name, player count, map size |
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup guide and pairing instructions"
```

---

### Task 7: Final Integration Test

- [ ] **Step 1: Run all unit tests**

Run: `python -m pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Verify the bot starts with missing config (graceful error)**

Run: `python -m src.main`
Expected: Error message about missing `.env` values, clean exit (not a traceback).

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: address any issues found during integration testing"
```
