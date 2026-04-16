import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from rustplus import RustError

import src.main as main_module
from src.main import poll_team_status, poll_server_info


def _make_member(steam_id, name, is_online=True, is_alive=True):
    m = MagicMock()
    m.steam_id = steam_id
    m.name = name
    m.is_online = is_online
    m.is_alive = is_alive
    return m


def _make_team_info(members):
    info = MagicMock()
    info.members = members
    return info


def _make_server_info(name="Test Server", players=100, max_players=200, size=4000,
                      wipe_time=None, logo_image=None):
    info = MagicMock()
    info.name = name
    info.players = players
    info.max_players = max_players
    info.size = size
    info.wipe_time = wipe_time
    info.logo_image = logo_image
    return info


class TestPollTeamStatus:
    """Tests for the team status polling loop."""

    @pytest.fixture(autouse=True)
    def reset_globals(self):
        """Reset global state before each test."""
        main_module._previous_online = set()
        main_module._previous_alive = {}
        yield
        main_module._previous_online = set()
        main_module._previous_alive = {}

    @pytest.mark.asyncio
    async def test_detects_player_coming_online(self):
        socket = AsyncMock()
        sender = AsyncMock()

        # Pre-seed: another player was online (so _previous_online is non-empty)
        main_module._previous_online = {99}
        main_module._previous_alive = {99: True}

        # Player comes online
        team = _make_team_info([
            _make_member(99, "Other", is_online=True),
            _make_member(1, "Alice", is_online=True),
        ])

        call_count = 0
        async def fake_get_team_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return team
            raise asyncio.CancelledError

        socket.get_team_info = fake_get_team_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_team_status(socket, sender)

        calls = [str(c) for c in sender.send.call_args_list]
        assert any("Online" in c or "connected" in c for c in calls)

    @pytest.mark.asyncio
    async def test_detects_player_going_offline(self):
        socket = AsyncMock()
        sender = AsyncMock()

        # Pre-seed: player was online
        main_module._previous_online = {1}
        main_module._previous_alive = {1: True}

        team = _make_team_info([_make_member(1, "Bob", is_online=False, is_alive=True)])

        call_count = 0
        async def fake_get_team_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return team
            raise asyncio.CancelledError

        socket.get_team_info = fake_get_team_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_team_status(socket, sender)

        calls = [str(c) for c in sender.send.call_args_list]
        assert any("Offline" in c or "disconnected" in c for c in calls)

    @pytest.mark.asyncio
    async def test_detects_player_death(self):
        socket = AsyncMock()
        sender = AsyncMock()

        # Pre-seed: player was alive
        main_module._previous_online = {1}
        main_module._previous_alive = {1: True}

        team = _make_team_info([_make_member(1, "Charlie", is_online=True, is_alive=False)])

        call_count = 0
        async def fake_get_team_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return team
            raise asyncio.CancelledError

        socket.get_team_info = fake_get_team_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_team_status(socket, sender)

        calls = [str(c) for c in sender.send.call_args_list]
        assert any("killed" in c or "Down" in c for c in calls)

    @pytest.mark.asyncio
    async def test_detects_player_respawn(self):
        socket = AsyncMock()
        sender = AsyncMock()

        # Pre-seed: player was dead
        main_module._previous_online = {1}
        main_module._previous_alive = {1: False}

        team = _make_team_info([_make_member(1, "Dave", is_online=True, is_alive=True)])

        call_count = 0
        async def fake_get_team_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return team
            raise asyncio.CancelledError

        socket.get_team_info = fake_get_team_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_team_status(socket, sender)

        calls = [str(c) for c in sender.send.call_args_list]
        assert any("Respawned" in c or "alive" in c for c in calls)

    @pytest.mark.asyncio
    async def test_handles_rust_error_gracefully(self):
        socket = AsyncMock()
        sender = AsyncMock()

        call_count = 0
        async def fake_get_team_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return RustError()
            raise asyncio.CancelledError

        socket.get_team_info = fake_get_team_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_team_status(socket, sender)

        sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_none_response(self):
        socket = AsyncMock()
        sender = AsyncMock()

        call_count = 0
        async def fake_get_team_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None
            raise asyncio.CancelledError

        socket.get_team_info = fake_get_team_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_team_status(socket, sender)

        sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_exception_and_continues(self):
        socket = AsyncMock()
        sender = AsyncMock()

        call_count = 0
        async def fake_get_team_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("test error")
            raise asyncio.CancelledError

        socket.get_team_info = fake_get_team_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_team_status(socket, sender)

        # Should not crash, just log and continue
        sender.send.assert_not_called()


class TestPollServerInfo:
    """Tests for the server info polling loop."""

    @pytest.mark.asyncio
    async def test_sends_server_info_on_change(self):
        socket = AsyncMock()
        sender = AsyncMock()

        info = _make_server_info(players=100, max_players=200)

        call_count = 0
        async def fake_get_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return info
            raise asyncio.CancelledError

        socket.get_info = fake_get_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_server_info(socket, sender)

        sender.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_resend_same_info(self):
        socket = AsyncMock()
        sender = AsyncMock()

        info = _make_server_info(players=100, max_players=200)

        call_count = 0
        async def fake_get_info():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return info
            raise asyncio.CancelledError

        socket.get_info = fake_get_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_server_info(socket, sender)

        # Only sends once since player count didn't change
        assert sender.send.call_count == 1

    @pytest.mark.asyncio
    async def test_resends_on_player_count_change(self):
        socket = AsyncMock()
        sender = AsyncMock()

        info1 = _make_server_info(players=100, max_players=200)
        info2 = _make_server_info(players=150, max_players=200)

        call_count = 0
        async def fake_get_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return info1
            if call_count == 2:
                return info2
            raise asyncio.CancelledError

        socket.get_info = fake_get_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_server_info(socket, sender)

        assert sender.send.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_rust_error(self):
        socket = AsyncMock()
        sender = AsyncMock()

        call_count = 0
        async def fake_get_info():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return RustError()
            raise asyncio.CancelledError

        socket.get_info = fake_get_info

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(asyncio.CancelledError):
                await poll_server_info(socket, sender)

        sender.send.assert_not_called()


class TestSmartAlarmFormatter:
    """Tests for the smart alarm formatter to ensure raid alerts work correctly."""

    def test_alarm_has_red_color(self):
        from src.formatter import format_smart_alarm
        result = format_smart_alarm("Base Under Attack!", "Explosions detected")
        embed = result["embeds"][0]
        assert embed["color"] == 0xFF0000

    def test_alarm_contains_alarm_name(self):
        from src.formatter import format_smart_alarm
        result = format_smart_alarm("TC Raid Alarm", "Someone is raiding!")
        embed = result["embeds"][0]
        assert "TC Raid Alarm" in embed["description"]

    def test_alarm_contains_message(self):
        from src.formatter import format_smart_alarm
        result = format_smart_alarm("Base Alert", "C4 detected nearby")
        embed = result["embeds"][0]
        assert "C4 detected nearby" in embed["description"]

    def test_alarm_title_says_alarm(self):
        from src.formatter import format_smart_alarm
        result = format_smart_alarm("Perimeter Breach", "Motion detected")
        embed = result["embeds"][0]
        assert "ALARM" in embed["title"]

    def test_alarm_has_timestamp(self):
        from src.formatter import format_smart_alarm
        result = format_smart_alarm("Raid Alarm", "alert")
        assert "timestamp" in result["embeds"][0]

    def test_alarm_has_footer(self):
        from src.formatter import format_smart_alarm
        result = format_smart_alarm("Raid Alarm", "alert")
        assert result["embeds"][0]["footer"]["text"] == "Smart Alarm"

    def test_alarm_different_names_produce_different_embeds(self):
        from src.formatter import format_smart_alarm
        r1 = format_smart_alarm("North Base", "alert")
        r2 = format_smart_alarm("South Base", "alert")
        assert r1["embeds"][0]["description"] != r2["embeds"][0]["description"]


class TestConnectionStatusFormatter:
    """Tests for connection status to ensure reconnect alerts work."""

    def test_connected_is_green(self):
        from src.formatter import format_connection_status
        result = format_connection_status(connected=True)
        assert result["embeds"][0]["color"] == 0x2ECC71

    def test_disconnected_is_red(self):
        from src.formatter import format_connection_status
        result = format_connection_status(connected=False)
        assert result["embeds"][0]["color"] == 0xE74C3C

    def test_connected_mentions_monitoring(self):
        from src.formatter import format_connection_status
        result = format_connection_status(connected=True)
        assert "monitoring" in result["embeds"][0]["description"].lower()

    def test_disconnected_mentions_reconnect(self):
        from src.formatter import format_connection_status
        result = format_connection_status(connected=False)
        assert "reconnect" in result["embeds"][0]["description"].lower()
