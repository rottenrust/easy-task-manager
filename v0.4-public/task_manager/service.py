from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from task_manager.storage import (
    STATUS_ACTIVE,
    STATUS_ARCHIVED,
    load_tasks,
    save_tasks,
)


class TaskService:
    def add_task(self, task_text: str) -> dict[str, Any]:
        return add_task(task_text)

    def list_active_tasks(self) -> list[dict[str, Any]]:
        return list_active_tasks()

    def archive_task(self, task_id: int) -> tuple[bool, str]:
        return archive_task(task_id)

    def list_archived_tasks(self) -> list[dict[str, Any]]:
        return list_archived_tasks()

    def delete_task(self, task_id: int) -> bool:
        return delete_task(task_id)

    def restore_task(self, task_id: int) -> tuple[dict[str, Any] | None, str]:
        return restore_task(task_id)

    def restore_last_archived_task(self) -> tuple[dict[str, Any] | None, str]:
        return restore_last_archived_task()

    def clear_archive(self) -> int:
        return clear_archive()


SERVICE = TaskService()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _next_id(tasks: list[dict[str, Any]]) -> int:
    if not tasks:
        return 1
    return max(task.get("id", 0) for task in tasks) + 1


def _find_task(tasks: list[dict[str, Any]], task_id: int) -> dict[str, Any] | None:
    return next((task for task in tasks if task.get("id") == task_id), None)


def add_task(task_text: str) -> dict[str, Any]:
    tasks = load_tasks()
    task = {
        "id": _next_id(tasks),
        "text": task_text,
        "status": STATUS_ACTIVE,
        "created_at": _utc_now_iso(),
        "completed_at": None,
    }
    tasks.append(task)
    save_tasks(tasks)
    return task


def list_active_tasks() -> list[dict[str, Any]]:
    tasks = load_tasks()
    return [task for task in tasks if task.get("status") == STATUS_ACTIVE]


def list_archived_tasks() -> list[dict[str, Any]]:
    tasks = load_tasks()
    return [task for task in tasks if task.get("status") == STATUS_ARCHIVED]


def archive_task(task_id: int) -> tuple[bool, str]:
    tasks = load_tasks()
    task = _find_task(tasks, task_id)
    if not task:
        return False, "not_found"

    if task.get("status") == STATUS_ARCHIVED:
        return False, "already_archived"

    task["status"] = STATUS_ARCHIVED
    task["completed_at"] = _utc_now_iso()
    save_tasks(tasks)
    return True, "archived"


def delete_task(task_id: int) -> bool:
    tasks = load_tasks()
    task = _find_task(tasks, task_id)
    if not task:
        return False

    updated = [item for item in tasks if item.get("id") != task_id]
    save_tasks(updated)
    return True


def restore_task(task_id: int) -> tuple[dict[str, Any] | None, str]:
    tasks = load_tasks()
    task = _find_task(tasks, task_id)
    if not task:
        return None, "not_found"

    if task.get("status") != STATUS_ARCHIVED:
        return None, "not_archived"

    task["status"] = STATUS_ACTIVE
    task["completed_at"] = None
    save_tasks(tasks)
    return task, "restored"


def restore_last_archived_task() -> tuple[dict[str, Any] | None, str]:
    tasks = load_tasks()
    archived = [task for task in tasks if task.get("status") == STATUS_ARCHIVED]
    if not archived:
        return None, "archive_empty"

    task = archived[-1]
    task["status"] = STATUS_ACTIVE
    task["completed_at"] = None
    save_tasks(tasks)
    return task, "restored"


def clear_archive() -> int:
    tasks = load_tasks()
    active_tasks = [task for task in tasks if task.get("status") == STATUS_ACTIVE]
    removed_count = len(tasks) - len(active_tasks)
    if removed_count == 0:
        return 0

    save_tasks(active_tasks)
    return removed_count
