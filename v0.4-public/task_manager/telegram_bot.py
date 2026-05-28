from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from task_manager.service import SERVICE
from task_manager.telegram_client import TelegramBotClient

LOG_FILE = Path(__file__).resolve().parent.parent / "task_manager.log"
LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    LOGGER.setLevel(logging.INFO)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    LOGGER.addHandler(file_handler)

START_MESSAGE = "Привет!\nЯ помогаю вести личный список задач."
HELP_MESSAGE = (
    "Доступные команды:\n"
    "/start — приветствие и краткое описание бота\n"
    "/help — список доступных команд\n"
    "/add <текст> — добавить новую задачу\n"
    "/today — показать активные задачи\n"
    "/list — показать активные задачи\n"
    "/done <id> — завершить задачу\n"
    "/archive — показать выполненные задачи\n"
    "/delete <id> — удалить задачу\n"
    "/undo [id] — восстановить завершенную задачу\n"
    "/clear_archive — очистить архив"
)
ACCESS_DENIED_MESSAGE = "Доступ запрещен: бот доступен только владельцу."
ADD_USAGE_MESSAGE = "Использование: /add <текст задачи>"
ADD_SUCCESS_MESSAGE_TEMPLATE = "Задача добавлена: #{task_id} — {task_text}"
DONE_USAGE_MESSAGE = "Использование: /done <id задачи>"
DONE_SUCCESS_MESSAGE_TEMPLATE = "Задача завершена: #{task_id}"
DONE_NOT_FOUND_MESSAGE = "Задача не найдена."
DONE_ALREADY_DONE_MESSAGE = "Задача уже завершена."
DELETE_USAGE_MESSAGE = "Использование: /delete <id задачи>"
DELETE_SUCCESS_MESSAGE_TEMPLATE = "Задача удалена: #{task_id}"
DELETE_NOT_FOUND_MESSAGE = "Задача для удаления не найдена."
UNDO_USAGE_MESSAGE = "Использование: /undo или /undo <id задачи>"
UNDO_SUCCESS_MESSAGE_TEMPLATE = "Задача восстановлена: #{task_id}"
UNDO_NOT_FOUND_MESSAGE = "Задача для восстановления не найдена."
UNDO_NOT_ARCHIVED_MESSAGE = "Эта задача не находится в архиве."
UNDO_ARCHIVE_EMPTY_MESSAGE = "В архиве нет задач для восстановления."
CLEAR_ARCHIVE_SUCCESS_MESSAGE_TEMPLATE = "Архив очищен. Удалено задач: {count}."
CLEAR_ARCHIVE_EMPTY_MESSAGE = "Архив уже пуст."
ACTIVE_TASKS_EMPTY_MESSAGE = "Пока нет активных задач. Добавьте новую через /add <текст задачи>."
ACTIVE_TASKS_HEADER = "Активные задачи:"
ARCHIVE_TASKS_EMPTY_MESSAGE = "Архив пока пуст."
ARCHIVE_TASKS_HEADER = "Архив задач:"
UNKNOWN_COMMAND_MESSAGE = "Неизвестная команда. Используйте /help."


def _format_active_tasks_message() -> str:
    active_tasks = SERVICE.list_active_tasks()
    if not active_tasks:
        return ACTIVE_TASKS_EMPTY_MESSAGE

    lines = [ACTIVE_TASKS_HEADER]
    for task in active_tasks:
        lines.append(f"• #{task.get('id')} — {task.get('text')}")
    return "\n".join(lines)


def _format_archive_tasks_message() -> str:
    archived_tasks = SERVICE.list_archived_tasks()
    if not archived_tasks:
        return ARCHIVE_TASKS_EMPTY_MESSAGE

    lines = [ARCHIVE_TASKS_HEADER]
    for task in archived_tasks:
        lines.append(f"✓ #{task.get('id')} — {task.get('text')}")
    return "\n".join(lines)


def handle_update(client: TelegramBotClient, update: dict[str, Any]) -> bool:
    """Handle a single Telegram update.

    Returns True when a message was sent as a result of this update.
    """
    message = update.get("message")
    if not isinstance(message, dict):
        return False

    chat = message.get("chat")
    from_user = message.get("from")
    text = message.get("text")

    if not isinstance(chat, dict) or not isinstance(from_user, dict):
        return False

    chat_id = chat.get("id")
    user_id = from_user.get("id")
    if not isinstance(chat_id, int) or not isinstance(user_id, int):
        return False

    owner_id = TelegramBotClient.owner_id_from_env()
    if user_id != owner_id:
        LOGGER.warning("Access denied for user_id=%s", user_id)
        client.send_message(chat_id=chat_id, text=ACCESS_DENIED_MESSAGE)
        return True

    if not isinstance(text, str):
        return False

    normalized_text = text.strip()
    if not normalized_text:
        return False

    if normalized_text == "/start":
        LOGGER.info("Command /start user_id=%s", user_id)
        client.send_message(chat_id=chat_id, text=START_MESSAGE)
        return True

    if normalized_text == "/help":
        LOGGER.info("Command /help user_id=%s", user_id)
        client.send_message(chat_id=chat_id, text=HELP_MESSAGE)
        return True

    if normalized_text.startswith("/add"):
        payload = normalized_text[4:].strip()
        if not payload:
            LOGGER.info("Invalid /add payload user_id=%s", user_id)
            client.send_message(chat_id=chat_id, text=ADD_USAGE_MESSAGE)
            return True

        task = SERVICE.add_task(payload)
        LOGGER.info("Task added id=%s user_id=%s", task["id"], user_id)
        client.send_message(
            chat_id=chat_id,
            text=ADD_SUCCESS_MESSAGE_TEMPLATE.format(
                task_id=task["id"],
                task_text=task["text"],
            ),
        )
        return True

    if normalized_text in {"/today", "/list"}:
        LOGGER.info("Command %s user_id=%s", normalized_text, user_id)
        client.send_message(chat_id=chat_id, text=_format_active_tasks_message())
        return True

    if normalized_text == "/archive":
        LOGGER.info("Command /archive user_id=%s", user_id)
        client.send_message(chat_id=chat_id, text=_format_archive_tasks_message())
        return True

    if normalized_text.startswith("/delete"):
        payload = normalized_text[7:].strip()
        if not payload:
            LOGGER.info("Invalid /delete payload user_id=%s", user_id)
            client.send_message(chat_id=chat_id, text=DELETE_USAGE_MESSAGE)
            return True

        try:
            task_id = int(payload)
        except ValueError:
            LOGGER.info("Invalid /delete task_id=%s user_id=%s", payload, user_id)
            client.send_message(chat_id=chat_id, text=DELETE_USAGE_MESSAGE)
            return True

        if not SERVICE.delete_task(task_id):
            client.send_message(chat_id=chat_id, text=DELETE_NOT_FOUND_MESSAGE)
            return True

        LOGGER.info("Task deleted id=%s user_id=%s", task_id, user_id)
        client.send_message(
            chat_id=chat_id,
            text=DELETE_SUCCESS_MESSAGE_TEMPLATE.format(task_id=task_id),
        )
        return True

    if normalized_text.startswith("/done"):
        payload = normalized_text[5:].strip()
        if not payload:
            LOGGER.info("Invalid /done payload user_id=%s", user_id)
            client.send_message(chat_id=chat_id, text=DONE_USAGE_MESSAGE)
            return True

        try:
            task_id = int(payload)
        except ValueError:
            LOGGER.info("Invalid /done task_id=%s user_id=%s", payload, user_id)
            client.send_message(chat_id=chat_id, text=DONE_USAGE_MESSAGE)
            return True

        is_archived, status = SERVICE.archive_task(task_id)
        if is_archived:
            LOGGER.info("Task archived id=%s user_id=%s", task_id, user_id)
            client.send_message(
                chat_id=chat_id,
                text=DONE_SUCCESS_MESSAGE_TEMPLATE.format(
                    task_id=task_id,
                ),
            )
            return True

        if status == "not_found":
            client.send_message(chat_id=chat_id, text=DONE_NOT_FOUND_MESSAGE)
            return True

        if status == "already_archived":
            client.send_message(chat_id=chat_id, text=DONE_ALREADY_DONE_MESSAGE)
            return True

        client.send_message(chat_id=chat_id, text=DONE_NOT_FOUND_MESSAGE)
        return True

    if normalized_text.startswith("/undo"):
        payload = normalized_text[5:].strip()
        if not payload:
            task, status = SERVICE.restore_last_archived_task()
            if status == "archive_empty":
                client.send_message(chat_id=chat_id, text=UNDO_ARCHIVE_EMPTY_MESSAGE)
                return True

            if task is not None and status == "restored":
                LOGGER.info("Task restored last id=%s user_id=%s", task["id"], user_id)
                client.send_message(
                    chat_id=chat_id,
                    text=UNDO_SUCCESS_MESSAGE_TEMPLATE.format(task_id=task["id"]),
                )
                return True

            client.send_message(chat_id=chat_id, text=UNDO_ARCHIVE_EMPTY_MESSAGE)
            return True

        try:
            task_id = int(payload)
        except ValueError:
            LOGGER.info("Invalid /undo task_id=%s user_id=%s", payload, user_id)
            client.send_message(chat_id=chat_id, text=UNDO_USAGE_MESSAGE)
            return True

        task, status = SERVICE.restore_task(task_id)
        if task is not None and status == "restored":
            LOGGER.info("Task restored id=%s user_id=%s", task_id, user_id)
            client.send_message(
                chat_id=chat_id,
                text=UNDO_SUCCESS_MESSAGE_TEMPLATE.format(task_id=task_id),
            )
            return True

        if status == "not_found":
            client.send_message(chat_id=chat_id, text=UNDO_NOT_FOUND_MESSAGE)
            return True

        if status == "not_archived":
            client.send_message(chat_id=chat_id, text=UNDO_NOT_ARCHIVED_MESSAGE)
            return True

        client.send_message(chat_id=chat_id, text=UNDO_USAGE_MESSAGE)
        return True

    if normalized_text == "/clear_archive":
        removed_count = SERVICE.clear_archive()
        if removed_count == 0:
            client.send_message(chat_id=chat_id, text=CLEAR_ARCHIVE_EMPTY_MESSAGE)
            return True

        LOGGER.info("Archive cleared removed=%s user_id=%s", removed_count, user_id)
        client.send_message(
            chat_id=chat_id,
            text=CLEAR_ARCHIVE_SUCCESS_MESSAGE_TEMPLATE.format(count=removed_count),
        )
        return True

    if normalized_text.startswith("/"):
        LOGGER.info("Unknown command text=%s user_id=%s", normalized_text, user_id)
        client.send_message(chat_id=chat_id, text=UNKNOWN_COMMAND_MESSAGE)
        return True

    task = SERVICE.add_task(normalized_text)
    LOGGER.info("Task added by plain text id=%s user_id=%s", task["id"], user_id)
    client.send_message(
        chat_id=chat_id,
        text=ADD_SUCCESS_MESSAGE_TEMPLATE.format(
            task_id=task["id"],
            task_text=task["text"],
        ),
    )
    return True
