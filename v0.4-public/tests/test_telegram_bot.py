import os
import unittest
from unittest.mock import Mock, patch

from task_manager.telegram_bot import (
    ACCESS_DENIED_MESSAGE,
    ACTIVE_TASKS_EMPTY_MESSAGE,
    ACTIVE_TASKS_HEADER,
    ADD_SUCCESS_MESSAGE_TEMPLATE,
    ADD_USAGE_MESSAGE,
    ARCHIVE_TASKS_EMPTY_MESSAGE,
    ARCHIVE_TASKS_HEADER,
    CLEAR_ARCHIVE_EMPTY_MESSAGE,
    CLEAR_ARCHIVE_SUCCESS_MESSAGE_TEMPLATE,
    DELETE_NOT_FOUND_MESSAGE,
    DELETE_SUCCESS_MESSAGE_TEMPLATE,
    DELETE_USAGE_MESSAGE,
    HELP_MESSAGE,
    DONE_ALREADY_DONE_MESSAGE,
    DONE_NOT_FOUND_MESSAGE,
    DONE_SUCCESS_MESSAGE_TEMPLATE,
    DONE_USAGE_MESSAGE,
    START_MESSAGE,
    UNDO_ARCHIVE_EMPTY_MESSAGE,
    UNDO_NOT_ARCHIVED_MESSAGE,
    UNDO_NOT_FOUND_MESSAGE,
    UNDO_SUCCESS_MESSAGE_TEMPLATE,
    UNDO_USAGE_MESSAGE,
    UNKNOWN_COMMAND_MESSAGE,
    handle_update,
)
from task_manager.telegram_client import TELEGRAM_OWNER_ID_ENV


class TelegramBotHandlerTests(unittest.TestCase):
    def test_start_command_for_owner_sends_greeting(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/start",
            }
        }
        client = Mock()

        with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
            handled = handle_update(client, update)

        self.assertTrue(handled)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=START_MESSAGE,
        )

    def test_start_command_for_non_owner_sends_access_denied(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 43},
                "text": "/start",
            }
        }
        client = Mock()

        with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
            handled = handle_update(client, update)

        self.assertTrue(handled)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACCESS_DENIED_MESSAGE,
        )

    def test_help_command_for_owner_sends_help_message(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/help",
            }
        }
        client = Mock()

        with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
            handled = handle_update(client, update)

        self.assertTrue(handled)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=HELP_MESSAGE,
        )

    def test_help_command_for_non_owner_sends_access_denied(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 43},
                "text": "/help",
            }
        }
        client = Mock()

        with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
            handled = handle_update(client, update)

        self.assertTrue(handled)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACCESS_DENIED_MESSAGE,
        )

    def test_update_without_text_is_skipped(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
            }
        }
        client = Mock()

        with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
            handled = handle_update(client, update)

        self.assertFalse(handled)
        client.send_message.assert_not_called()

    def test_add_command_for_owner_adds_task(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/add Купить хлеб",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.add_task") as add_task_mock:
            add_task_mock.return_value = {"id": 10, "text": "Купить хлеб"}
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        add_task_mock.assert_called_once_with("Купить хлеб")
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ADD_SUCCESS_MESSAGE_TEMPLATE.format(
                task_id=10,
                task_text="Купить хлеб",
            ),
        )

    def test_add_command_without_text_for_owner_returns_usage(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/add",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.add_task") as add_task_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        add_task_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ADD_USAGE_MESSAGE,
        )

    def test_plain_text_message_for_owner_adds_task(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "Купить воду",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.add_task") as add_task_mock:
            add_task_mock.return_value = {"id": 11, "text": "Купить воду"}
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        add_task_mock.assert_called_once_with("Купить воду")
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ADD_SUCCESS_MESSAGE_TEMPLATE.format(
                task_id=11,
                task_text="Купить воду",
            ),
        )

    def test_plain_text_message_for_non_owner_sends_access_denied(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 43},
                "text": "Купить воду",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.add_task") as add_task_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        add_task_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACCESS_DENIED_MESSAGE,
        )

    def test_plain_whitespace_message_for_owner_is_skipped(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "   ",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.add_task") as add_task_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertFalse(handled)
        add_task_mock.assert_not_called()
        client.send_message.assert_not_called()

    def test_today_command_for_owner_returns_active_tasks(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/today",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.list_active_tasks") as list_mock:
            list_mock.return_value = [
                {"id": 10, "text": "Купить хлеб"},
                {"id": 11, "text": "Позвонить маме"},
            ]
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        list_mock.assert_called_once_with()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=(
                f"{ACTIVE_TASKS_HEADER}\n"
                "• #10 — Купить хлеб\n"
                "• #11 — Позвонить маме"
            ),
        )

    def test_list_command_for_owner_returns_empty_message(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/list",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.list_active_tasks") as list_mock:
            list_mock.return_value = []
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        list_mock.assert_called_once_with()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACTIVE_TASKS_EMPTY_MESSAGE,
        )

    def test_today_command_for_owner_returns_empty_message(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/today",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.list_active_tasks") as list_mock:
            list_mock.return_value = []
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        list_mock.assert_called_once_with()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACTIVE_TASKS_EMPTY_MESSAGE,
        )

    def test_today_command_for_non_owner_sends_access_denied(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 43},
                "text": "/today",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.list_active_tasks") as list_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        list_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACCESS_DENIED_MESSAGE,
        )

    def test_done_command_for_owner_archives_task(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/done 10",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.archive_task") as archive_mock:
            archive_mock.return_value = (True, "archived")
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        archive_mock.assert_called_once_with(10)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DONE_SUCCESS_MESSAGE_TEMPLATE.format(task_id=10),
        )

    def test_done_command_without_id_for_owner_returns_usage(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/done",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.archive_task") as archive_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        archive_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DONE_USAGE_MESSAGE,
        )

    def test_done_command_with_invalid_id_for_owner_returns_usage(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/done abc",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.archive_task") as archive_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        archive_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DONE_USAGE_MESSAGE,
        )

    def test_done_command_for_owner_when_task_not_found(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/done 999",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.archive_task") as archive_mock:
            archive_mock.return_value = (False, "not_found")
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        archive_mock.assert_called_once_with(999)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DONE_NOT_FOUND_MESSAGE,
        )

    def test_done_command_for_owner_when_task_already_archived(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/done 10",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.archive_task") as archive_mock:
            archive_mock.return_value = (False, "already_archived")
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        archive_mock.assert_called_once_with(10)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DONE_ALREADY_DONE_MESSAGE,
        )

    def test_done_command_for_non_owner_sends_access_denied(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 43},
                "text": "/done 10",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.archive_task") as archive_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        archive_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACCESS_DENIED_MESSAGE,
        )

    def test_archive_command_for_owner_returns_archived_tasks(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/archive",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.list_archived_tasks") as list_mock:
            list_mock.return_value = [
                {"id": 8, "text": "Сходить в аптеку"},
                {"id": 9, "text": "Оплатить интернет"},
            ]
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        list_mock.assert_called_once_with()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=(
                f"{ARCHIVE_TASKS_HEADER}\n"
                "✓ #8 — Сходить в аптеку\n"
                "✓ #9 — Оплатить интернет"
            ),
        )

    def test_archive_command_for_owner_returns_empty_message(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/archive",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.list_archived_tasks") as list_mock:
            list_mock.return_value = []
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        list_mock.assert_called_once_with()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ARCHIVE_TASKS_EMPTY_MESSAGE,
        )

    def test_archive_command_for_non_owner_sends_access_denied(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 43},
                "text": "/archive",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.list_archived_tasks") as list_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        list_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACCESS_DENIED_MESSAGE,
        )

    def test_delete_command_for_owner_deletes_task(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/delete 10",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.delete_task") as delete_mock:
            delete_mock.return_value = True
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        delete_mock.assert_called_once_with(10)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DELETE_SUCCESS_MESSAGE_TEMPLATE.format(task_id=10),
        )

    def test_delete_command_for_owner_with_invalid_id_returns_usage(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/delete abc",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.delete_task") as delete_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        delete_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DELETE_USAGE_MESSAGE,
        )

    def test_delete_command_for_owner_without_id_returns_usage(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/delete",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.delete_task") as delete_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        delete_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DELETE_USAGE_MESSAGE,
        )

    def test_delete_command_for_owner_when_not_found(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/delete 999",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.delete_task") as delete_mock:
            delete_mock.return_value = False
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        delete_mock.assert_called_once_with(999)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=DELETE_NOT_FOUND_MESSAGE,
        )

    def test_undo_command_for_owner_restores_last_archived_task(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/undo",
            }
        }
        client = Mock()

        with patch(
            "task_manager.telegram_bot.SERVICE.restore_last_archived_task"
        ) as restore_mock:
            restore_mock.return_value = ({"id": 8}, "restored")
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        restore_mock.assert_called_once_with()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=UNDO_SUCCESS_MESSAGE_TEMPLATE.format(task_id=8),
        )

    def test_undo_command_for_owner_when_archive_is_empty(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/undo",
            }
        }
        client = Mock()

        with patch(
            "task_manager.telegram_bot.SERVICE.restore_last_archived_task"
        ) as restore_mock:
            restore_mock.return_value = (None, "archive_empty")
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=UNDO_ARCHIVE_EMPTY_MESSAGE,
        )

    def test_undo_command_with_id_for_owner_restores_task(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/undo 11",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.restore_task") as restore_mock:
            restore_mock.return_value = ({"id": 11}, "restored")
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        restore_mock.assert_called_once_with(11)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=UNDO_SUCCESS_MESSAGE_TEMPLATE.format(task_id=11),
        )

    def test_undo_command_with_id_for_owner_when_not_found(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/undo 55",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.restore_task") as restore_mock:
            restore_mock.return_value = (None, "not_found")
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=UNDO_NOT_FOUND_MESSAGE,
        )

    def test_undo_command_with_id_for_owner_when_not_archived(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/undo 7",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.restore_task") as restore_mock:
            restore_mock.return_value = (None, "not_archived")
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=UNDO_NOT_ARCHIVED_MESSAGE,
        )

    def test_undo_command_with_id_for_owner_with_invalid_id_returns_usage(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/undo abc",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.restore_task") as restore_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        restore_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=UNDO_USAGE_MESSAGE,
        )

    def test_undo_command_for_non_owner_sends_access_denied(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 43},
                "text": "/undo",
            }
        }
        client = Mock()

        with patch(
            "task_manager.telegram_bot.SERVICE.restore_last_archived_task"
        ) as restore_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        restore_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACCESS_DENIED_MESSAGE,
        )

    def test_clear_archive_for_owner_with_non_empty_archive(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/clear_archive",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.clear_archive") as clear_mock:
            clear_mock.return_value = 3
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        clear_mock.assert_called_once_with()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=CLEAR_ARCHIVE_SUCCESS_MESSAGE_TEMPLATE.format(count=3),
        )

    def test_clear_archive_for_owner_when_archive_is_empty(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/clear_archive",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.clear_archive") as clear_mock:
            clear_mock.return_value = 0
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=CLEAR_ARCHIVE_EMPTY_MESSAGE,
        )

    def test_clear_archive_for_non_owner_sends_access_denied(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 43},
                "text": "/clear_archive",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.clear_archive") as clear_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        clear_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=ACCESS_DENIED_MESSAGE,
        )

    def test_unknown_slash_command_returns_error_and_does_not_add_task(self) -> None:
        update = {
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42},
                "text": "/foo",
            }
        }
        client = Mock()

        with patch("task_manager.telegram_bot.SERVICE.add_task") as add_task_mock:
            with patch.dict(os.environ, {TELEGRAM_OWNER_ID_ENV: "42"}, clear=True):
                handled = handle_update(client, update)

        self.assertTrue(handled)
        add_task_mock.assert_not_called()
        client.send_message.assert_called_once_with(
            chat_id=100,
            text=UNKNOWN_COMMAND_MESSAGE,
        )


if __name__ == "__main__":
    unittest.main()
