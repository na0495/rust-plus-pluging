import asyncio
import logging
import sys

from rustplus import RustSocket, ServerDetails, ChatEvent, TeamEvent, EntityEvent, RustError

from src.config import load_config, ConfigError
from src.formatter import (
    format_chat_message,
    format_player_online,
    format_player_offline,
    format_player_death,
    format_player_respawned,
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
            if team_info is None or isinstance(team_info, RustError):
                await asyncio.sleep(30)
                continue

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

                # Death / respawn detection
                was_alive = _previous_alive.get(steam_id)
                if was_alive is True and not is_alive:
                    await sender.send(format_player_death(name))
                elif was_alive is False and is_alive:
                    await sender.send(format_player_respawned(name))
                _previous_alive[steam_id] = is_alive

            _previous_online = current_online

        except Exception as e:
            logger.error("Error polling team status: %s", e)

        await asyncio.sleep(30)


async def poll_server_info(socket: RustSocket, sender: DiscordSender):
    """Poll server info every 10 minutes and report on changes."""
    _last_info = None

    while True:
        try:
            info = await socket.get_info()
            if info is None or isinstance(info, RustError):
                await asyncio.sleep(600)
                continue
            summary = f"{info.players}/{info.max_players}"

            if summary != _last_info:
                await sender.send(format_server_info(
                    name=info.name,
                    players=info.players,
                    max_players=info.max_players,
                    map_size=info.size,
                    wipe_time=getattr(info, "wipe_time", None),
                    logo=getattr(info, "logo_image", None),
                ))
                _last_info = summary

        except Exception as e:
            logger.error("Error polling server info: %s", e)

        await asyncio.sleep(600)


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

            # Register team event handler (joins/leaves)
            @TeamEvent(server_details)
            async def on_team(event):
                logger.info("Team event received")

            # Start polling tasks
            team_task = asyncio.create_task(poll_team_status(socket, sender))
            server_task = asyncio.create_task(poll_server_info(socket, sender))

            # Keep running until disconnected
            await asyncio.gather(team_task, server_task)

        except Exception as e:
            logger.error("Connection error: %s", e)
            try:
                await sender.send(format_connection_status(connected=False))
            except Exception:
                pass
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
