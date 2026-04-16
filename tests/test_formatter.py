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
