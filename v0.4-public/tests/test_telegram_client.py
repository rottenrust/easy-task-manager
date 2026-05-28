import json
import os
import socket
import unittest
from unittest.mock import patch

from task_manager.telegram_client import (
    TELEGRAM_BOT_TOKEN_ENV,
    TELEGRAM_OWNER_ID_ENV,
    TelegramAPIError,
    TelegramBotClient,
    TelegramTimeoutError,
)


class _Response:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


class TelegramBotClientTests(unittest.TestCase):
    def test_init_rejects_empty_token(self) -> None:
        with self.assertRaises(ValueError):
            TelegramBotClient("   ")

    def test_from_env_uses_telegram_bot_token(self) -> None:
        with patch.dict(os.environ, {TELEGRAM_BOT_TOKEN_ENV: "abc123"}, clear=True):
            client = TelegramBotClient.from_env()

        self.assertTrue(client._base_url.endswith("/botabc123"))

    def test_from_env_raises_when_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                ValueError, "TELEGRAM_BOT_TOKEN environment variable"
            ):
                TelegramBotClient.from_env()

    def test_from_env_raises_when_empty(self) -> None:
        with patch.dict(os.environ, {TELEGRAM_BOT_TOKEN_ENV: "   "}, clear=True):
            with self.assertRaisesRegex(
                ValueError, "TELEGRAM_BOT_TOKEN environment variable"
            ):
                TelegramBotClient.from_env()

    def test_owner_id_from_env_returns_integer(self) -> None:
        with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "123456"}, clear=True):
            owner_id = TelegramBotClient.owner_id_from_env()

        self.assertEqual(owner_id, 123456)

    def test_owner_id_from_env_raises_when_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                ValueError, "TELEGRAM_OWNER_ID environment variable"
            ):
                TelegramBotClient.owner_id_from_env()

    def test_owner_id_from_env_raises_when_empty(self) -> None:
        with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "   "}, clear=True):
            with self.assertRaisesRegex(
                ValueError, "TELEGRAM_OWNER_ID environment variable"
            ):
                TelegramBotClient.owner_id_from_env()

    def test_owner_id_from_env_raises_when_non_numeric(self) -> None:
        with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "abc"}, clear=True):
            with self.assertRaisesRegex(ValueError, "must be an integer"):
                TelegramBotClient.owner_id_from_env()

    @patch("task_manager.telegram_client.request.urlopen")
    def test_get_updates_returns_result(self, mocked_urlopen) -> None:
        mocked_urlopen.return_value = _Response(
            {"ok": True, "result": [{"update_id": 1}]}
        )
        client = TelegramBotClient("token")

        updates = client.get_updates(offset=100)

        self.assertEqual(updates, [{"update_id": 1}])

    @patch("task_manager.telegram_client.request.urlopen")
    def test_send_message_returns_result(self, mocked_urlopen) -> None:
        mocked_urlopen.return_value = _Response(
            {"ok": True, "result": {"message_id": 42}}
        )
        client = TelegramBotClient("token")

        result = client.send_message(chat_id=7, text="hello")

        self.assertEqual(result, {"message_id": 42})

    @patch("task_manager.telegram_client.request.urlopen")
    def test_call_raises_for_api_error(self, mocked_urlopen) -> None:
        mocked_urlopen.return_value = _Response(
            {"ok": False, "description": "Bad Request"}
        )
        client = TelegramBotClient("token")

        with self.assertRaises(TelegramAPIError):
            client.get_updates()

    @patch("task_manager.telegram_client.request.urlopen")
    def test_call_raises_timeout_error_for_socket_timeout(self, mocked_urlopen) -> None:
        mocked_urlopen.side_effect = socket.timeout("timed out")
        client = TelegramBotClient("token")

        with self.assertRaises(TelegramTimeoutError):
            client.get_updates()


if __name__ == "__main__":
    unittest.main()
