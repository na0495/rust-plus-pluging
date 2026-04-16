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


class TestFormatChatMessage:
    def test_is_embed_with_blue_color(self):
        result = format_chat_message("PlayerOne", "hello team")
        embed = result["embeds"][0]
        assert embed["color"] == 0x3498DB
        assert "PlayerOne" in embed["description"]
        assert "hello team" in embed["description"]

    def test_has_title(self):
        result = format_chat_message("PlayerOne", "hello")
        assert "Chat" in result["embeds"][0]["title"]


class TestFormatPlayerOnline:
    def test_green_embed(self):
        result = format_player_online("PlayerOne")
        embed = result["embeds"][0]
        assert embed["color"] == 0x2ECC71
        assert "PlayerOne" in embed["description"]

    def test_has_title_and_footer(self):
        result = format_player_online("PlayerOne")
        embed = result["embeds"][0]
        assert "title" in embed
        assert "footer" in embed

    def test_has_timestamp(self):
        result = format_player_online("PlayerOne")
        assert "timestamp" in result["embeds"][0]


class TestFormatPlayerOffline:
    def test_gray_embed(self):
        result = format_player_offline("PlayerOne")
        embed = result["embeds"][0]
        assert embed["color"] == 0x95A5A6
        assert "PlayerOne" in embed["description"]


class TestFormatPlayerDeath:
    def test_red_embed(self):
        result = format_player_death("PlayerOne")
        embed = result["embeds"][0]
        assert embed["color"] == 0xE74C3C
        assert "PlayerOne" in embed["description"]

    def test_has_urgent_title(self):
        result = format_player_death("PlayerOne")
        embed = result["embeds"][0]
        assert "Down" in embed["title"] or "killed" in embed["description"].lower()


class TestFormatPlayerRespawned:
    def test_green_embed(self):
        result = format_player_respawned("PlayerOne")
        embed = result["embeds"][0]
        assert embed["color"] == 0x2ECC71
        assert "PlayerOne" in embed["description"]


class TestFormatSmartAlarm:
    def test_red_embed_with_alarm_name(self):
        result = format_smart_alarm("Base Raid Alarm", "alert")
        embed = result["embeds"][0]
        assert embed["color"] == 0xFF0000
        assert "Base Raid Alarm" in embed["description"]

    def test_has_alarm_title(self):
        result = format_smart_alarm("Base Raid Alarm", "alert")
        assert "ALARM" in result["embeds"][0]["title"]


class TestFormatServerInfo:
    def test_orange_embed_with_fields(self):
        result = format_server_info(
            name="Rustopia US Main",
            players=200,
            max_players=300,
            map_size=4000,
        )
        embed = result["embeds"][0]
        assert embed["color"] == 0xF39C12
        assert "fields" in embed
        assert any("200" in f["value"] for f in embed["fields"])

    def test_includes_server_name_in_title(self):
        result = format_server_info(
            name="Rustopia US Main",
            players=200,
            max_players=300,
            map_size=4000,
        )
        assert "Rustopia US Main" in result["embeds"][0]["title"]

    def test_includes_player_bar(self):
        result = format_server_info(
            name="Test",
            players=50,
            max_players=100,
            map_size=4000,
        )
        fields = result["embeds"][0]["fields"]
        player_field = [f for f in fields if "Players" in f["name"]][0]
        assert "50" in player_field["value"]

    def test_includes_wipe_time_when_provided(self):
        result = format_server_info(
            name="Test",
            players=50,
            max_players=100,
            map_size=4000,
            wipe_time=1775743130,
        )
        fields = result["embeds"][0]["fields"]
        wipe_field = [f for f in fields if "Wipe" in f["name"]]
        assert len(wipe_field) == 1

    def test_includes_logo_as_thumbnail(self):
        result = format_server_info(
            name="Test",
            players=50,
            max_players=100,
            map_size=4000,
            logo="https://example.com/logo.png",
        )
        assert result["embeds"][0]["thumbnail"]["url"] == "https://example.com/logo.png"


class TestFormatConnectionStatus:
    def test_disconnected_red(self):
        result = format_connection_status(connected=False)
        embed = result["embeds"][0]
        assert embed["color"] == 0xE74C3C

    def test_reconnected_green(self):
        result = format_connection_status(connected=True)
        embed = result["embeds"][0]
        assert embed["color"] == 0x2ECC71
