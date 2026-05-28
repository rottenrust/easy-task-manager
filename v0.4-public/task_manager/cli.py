from __future__ import annotations

import argparse
import logging

from task_manager.service import SERVICE
from task_manager.telegram_client import TelegramAPIError
from task_manager.telegram_polling import run_long_polling

LOGGER = logging.getLogger(__name__)


def cmd_add(task_text: str) -> None:
    task_text = task_text.strip()
    if not task_text:
        print("Task description cannot be empty.")
        return

    task = SERVICE.add_task(task_text)
    print(f"Added task #{task['id']}: {task['text']}")


def cmd_list() -> None:
    active_tasks = SERVICE.list_active_tasks()
    if not active_tasks:
        print("No tasks yet.")
        return

    for task in active_tasks:
        print(f"[ ] {task.get('id')}: {task.get('text')}")


def cmd_done(task_id: int) -> None:
    ok, status = SERVICE.archive_task(task_id)
    if not ok and status == "not_found":
        print(f"Task #{task_id} not found.")
        return
    if not ok and status == "already_archived":
        print(f"Task #{task_id} is already archived.")
        return

    print(f"Archived task #{task_id}.")


def cmd_delete(task_id: int) -> None:
    if not SERVICE.delete_task(task_id):
        print(f"Task #{task_id} not found.")
        return

    print(f"Deleted task #{task_id}.")


def cmd_telegram() -> None:
    try:
        run_long_polling(timeout=30)
    except KeyboardInterrupt:
        print("Bot stopped.")
    except (ValueError, TelegramAPIError) as exc:
        LOGGER.exception("Telegram polling failed at startup/runtime: %s", exc)
        print(f"Telegram polling failed: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Small CLI task manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("text", help="Task description")

    subparsers.add_parser("list", help="List all tasks")

    done_parser = subparsers.add_parser("done", help="Archive a task")
    done_parser.add_argument("id", type=int, help="Task id")

    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", type=int, help="Task id")
    subparsers.add_parser("telegram", help="Run Telegram bot via long polling")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args.text)
    elif args.command == "list":
        cmd_list()
    elif args.command == "done":
        cmd_done(args.id)
    elif args.command == "delete":
        cmd_delete(args.id)
    elif args.command == "telegram":
        cmd_telegram()


if __name__ == "__main__":
    main()
