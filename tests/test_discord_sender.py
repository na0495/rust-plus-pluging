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
