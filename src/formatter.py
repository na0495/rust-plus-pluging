from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _embed(
    description: str,
    color: int,
    title: str | None = None,
    footer: str | None = None,
    thumbnail: str | None = None,
    fields: list[dict] | None = None,
    author: dict | None = None,
) -> dict:
    embed = {
        "description": description,
        "color": color,
        "timestamp": _timestamp(),
    }
    if title:
        embed["title"] = title
    if footer:
        embed["footer"] = {"text": footer}
    if thumbnail:
        embed["thumbnail"] = {"url": thumbnail}
    if fields:
        embed["fields"] = fields
    if author:
        embed["author"] = author
    return {"embeds": [embed]}


# ── Team Chat ──────────────────────────────────────────────

def format_chat_message(player_name: str, message: str) -> dict:
    return _embed(
        title="\U0001f4ac Team Chat",
        description=f"**{player_name}**\n>>> {message}",
        color=0x3498DB,
        footer="Team Chat",
    )


# ── Player Online / Offline ───────────────────────────────

def format_player_online(player_name: str) -> dict:
    return _embed(
        title="\U0001f7e2 Player Online",
        description=f"**{player_name}** just connected to the server",
        color=0x2ECC71,
        footer="Player Status",
    )


def format_player_offline(player_name: str) -> dict:
    return _embed(
        title="\U0001f534 Player Offline",
        description=f"**{player_name}** disconnected from the server",
        color=0x95A5A6,
        footer="Player Status",
    )


# ── Player Death ──────────────────────────────────────────

def format_player_death(player_name: str) -> dict:
    return _embed(
        title="\U0001f480 Team Member Down!",
        description=f"**{player_name}** has been killed!",
        color=0xE74C3C,
        footer="Death Alert",
    )


# ── Player Respawned ─────────────────────────────────────

def format_player_respawned(player_name: str) -> dict:
    return _embed(
        title="\U0001f3e5 Player Respawned",
        description=f"**{player_name}** is back alive",
        color=0x2ECC71,
        footer="Player Status",
    )


# ── Smart Alarm ───────────────────────────────────────────

def format_smart_alarm(alarm_name: str, message: str) -> dict:
    return _embed(
        title="\U0001f6a8 ALARM TRIGGERED",
        description=(
            f"**{alarm_name}**\n"
            f">>> {message}"
        ),
        color=0xFF0000,
        footer="Smart Alarm",
    )


# ── Server Info ───────────────────────────────────────────

def format_server_info(
    name: str,
    players: int,
    max_players: int,
    map_size: int,
    wipe_time: int | None = None,
    logo: str | None = None,
) -> dict:
    fill = players / max_players if max_players else 0
    bar_filled = round(fill * 10)
    bar_empty = 10 - bar_filled
    bar = "\U0001f7e9" * bar_filled + "\U00002b1c" * bar_empty

    fields = [
        {"name": "\U0001f465 Players", "value": f"**{players}** / {max_players}\n{bar}", "inline": True},
        {"name": "\U0001f5fa Map Size", "value": f"**{map_size}**", "inline": True},
    ]

    if wipe_time:
        fields.append(
            {"name": "\U0001f4c5 Last Wipe", "value": f"<t:{wipe_time}:R>", "inline": True}
        )

    return _embed(
        title=f"\U0001f3ae {name}",
        description="",
        color=0xF39C12,
        fields=fields,
        footer="Server Info",
        thumbnail=logo,
    )


# ── Connection Status ─────────────────────────────────────

def format_connection_status(connected: bool) -> dict:
    if connected:
        return _embed(
            title="\u2705 Bot Connected",
            description="Rust+ bot is now connected and monitoring events",
            color=0x2ECC71,
            footer="Bot Status",
        )
    return _embed(
        title="\u274c Bot Disconnected",
        description="Rust+ bot lost connection — attempting to reconnect...",
        color=0xE74C3C,
        footer="Bot Status",
    )
