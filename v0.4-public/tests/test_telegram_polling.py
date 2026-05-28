import unittest
from unittest.mock import Mock, call, patch

from task_manager.telegram_polling import run_long_polling
from task_manager.telegram_client import TelegramTimeoutError


class TelegramPollingTests(unittest.TestCase):
    @patch("task_manager.telegram_polling.handle_update")
    @patch("task_manager.telegram_polling.TelegramBotClient")
    def test_run_long_polling_updates_offset_and_handles_each_update(
        self, client_cls_mock, handle_update_mock
    ) -> None:
        client = Mock()
        client_cls_mock.from_env.return_value = client
        client.get_updates.side_effect = [
            [{"update_id": 10}, {"update_id": 11}],
            KeyboardInterrupt(),
        ]

        with self.assertRaises(KeyboardInterrupt):
            run_long_polling(timeout=30)

        self.assertEqual(
            client.get_updates.call_args_list,
            [
                call(offset=None, timeout=30),
                call(offset=12, timeout=30),
            ],
        )
        self.assertEqual(handle_update_mock.call_count, 2)

    @patch("task_manager.telegram_polling.handle_update")
    @patch("task_manager.telegram_polling.TelegramBotClient")
    def test_run_long_polling_keeps_offset_when_update_id_is_invalid(
        self, client_cls_mock, handle_update_mock
    ) -> None:
        client = Mock()
        client_cls_mock.from_env.return_value = client
        client.get_updates.side_effect = [
            [{"update_id": "bad"}],
            KeyboardInterrupt(),
        ]

        with self.assertRaises(KeyboardInterrupt):
            run_long_polling(timeout=15)

        self.assertEqual(
            client.get_updates.call_args_list,
            [
                call(offset=None, timeout=15),
                call(offset=None, timeout=15),
            ],
        )
        handle_update_mock.assert_called_once_with(client, {"update_id": "bad"})

    @patch("task_manager.telegram_polling.handle_update")
    @patch("task_manager.telegram_polling.TelegramBotClient")
    def test_run_long_polling_retries_after_timeout(
        self, client_cls_mock, handle_update_mock
    ) -> None:
        client = Mock()
        client_cls_mock.from_env.return_value = client
        client.get_updates.side_effect = [
            TelegramTimeoutError("timeout"),
            [{"update_id": 20}],
            KeyboardInterrupt(),
        ]

        with self.assertRaises(KeyboardInterrupt):
            run_long_polling(timeout=20)

        self.assertEqual(
            client.get_updates.call_args_list,
            [
                call(offset=None, timeout=20),
                call(offset=None, timeout=20),
                call(offset=21, timeout=20),
            ],
        )
        handle_update_mock.assert_called_once_with(client, {"update_id": 20})

    @patch("task_manager.telegram_polling.handle_update")
    @patch("task_manager.telegram_polling.TelegramBotClient")
    def test_run_long_polling_continues_when_handler_fails(
        self, client_cls_mock, handle_update_mock
    ) -> None:
        client = Mock()
        client_cls_mock.from_env.return_value = client
        client.get_updates.side_effect = [
            [{"update_id": 1}, {"update_id": 2}],
            KeyboardInterrupt(),
        ]
        handle_update_mock.side_effect = [RuntimeError("boom"), None]

        with self.assertRaises(KeyboardInterrupt):
            run_long_polling(timeout=10)

        self.assertEqual(
            client.get_updates.call_args_list,
            [
                call(offset=None, timeout=10),
                call(offset=3, timeout=10),
            ],
        )
        self.assertEqual(handle_update_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
