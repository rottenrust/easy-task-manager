from __future__ import annotations

import json
import os
import socket
from typing import Any
from urllib import error, parse, request

TELEGRAM_BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
TELEGRAM_OWNER_ID_ENV = "TELEGRAM_OWNER_ID"


class TelegramAPIError(Exception):
    """Raised when Telegram Bot API returns an error response."""


class TelegramTimeoutError(TelegramAPIError):
    """Raised when Telegram request times out."""


class TelegramBotClient:
    def __init__(self, token: str, timeout: float = 30.0, request_timeout: float = 35.0) -> None:
        token = token.strip()
        if not token:
            raise ValueError("Telegram bot token cannot be empty")

        self._base_url = f"https://api.telegram.org/bot{token}"
        self._timeout = timeout
        self._request_timeout = request_timeout

    @classmethod
    def from_env(
        cls,
        env_var: str = TELEGRAM_BOT_TOKEN_ENV,
        timeout: float = 30.0,
        request_timeout: float = 35.0,
    ) -> "TelegramBotClient":
        token = os.getenv(env_var, "").strip()
        if not token:
            raise ValueError(
                f"Telegram bot token is not configured. "
                f"Set the {env_var} environment variable."
            )
        return cls(token=token, timeout=timeout, request_timeout=request_timeout)

    @staticmethod
    def owner_id_from_env(env_var: str = TELEGRAM_OWNER_ID_ENV) -> int:
        raw_owner_id = os.getenv(env_var, "").strip()
        if not raw_owner_id:
            raise ValueError(
                f"Telegram owner id is not configured. "
                f"Set the {env_var} environment variable."
            )

        try:
            return int(raw_owner_id)
        except ValueError as exc:
            raise ValueError(
                f"Telegram owner id must be an integer. "
                f"Invalid value in {env_var}."
            ) from exc

    def get_updates(
        self,
        offset: int | None = None,
        timeout: int = 30,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset

        response = self._call(
            "getUpdates",
            payload,
            request_timeout=max(self._request_timeout, float(timeout) + 5.0),
        )
        return response.get("result", [])

    def send_message(self, chat_id: int, text: str) -> dict[str, Any]:
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        response = self._call("sendMessage", payload, request_timeout=self._request_timeout)
        return response.get("result", {})

    def _call(
        self,
        method: str,
        payload: dict[str, Any],
        request_timeout: float,
    ) -> dict[str, Any]:
        body = parse.urlencode(payload).encode("utf-8")
        req = request.Request(
            f"{self._base_url}/{method}",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=request_timeout) as resp:
                raw = resp.read().decode("utf-8")
        except socket.timeout as exc:
            raise TelegramTimeoutError("Telegram API request timed out") from exc
        except error.URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise TelegramTimeoutError("Telegram API request timed out") from exc
            raise TelegramAPIError(f"Telegram API request failed: {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TelegramAPIError("Telegram API returned invalid JSON") from exc

        if not data.get("ok"):
            description = data.get("description", "unknown error")
            raise TelegramAPIError(f"Telegram API error: {description}")

        return data
