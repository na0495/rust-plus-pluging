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
