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
