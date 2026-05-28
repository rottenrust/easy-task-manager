from __future__ import annotations

import logging

from task_manager.telegram_bot import handle_update
from task_manager.telegram_client import (
    TelegramAPIError,
    TelegramBotClient,
    TelegramTimeoutError,
)


LOGGER = logging.getLogger(__name__)


def run_long_polling(timeout: int = 30) -> None:
    """Run Telegram long polling loop via getUpdates."""
    client = TelegramBotClient.from_env()
    offset: int | None = None

    while True:
        try:
            updates = client.get_updates(offset=offset, timeout=timeout)
        except TelegramTimeoutError:
            LOGGER.warning("Long polling network timeout, retrying")
            continue
        except TelegramAPIError as exc:
            LOGGER.exception("Telegram getUpdates failed: %s", exc)
            continue

        for update in updates:
            try:
                handle_update(client, update)
            except Exception as exc:
                LOGGER.exception("Failed to handle update: %s", exc)
            update_id = update.get("update_id")
            if isinstance(update_id, int):
                offset = update_id + 1
