from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


TASKS_FILE = Path(__file__).resolve().parent.parent / "tasks.json"
BACKUP_FILE = TASKS_FILE.with_name(f"{TASKS_FILE.name}.bak")
STATUS_ACTIVE = "active"
STATUS_ARCHIVED = "archived"
LEGACY_STATUS_COMPLETED = "completed"
VALID_STATUSES = {STATUS_ACTIVE, STATUS_ARCHIVED}
LOGGER = logging.getLogger(__name__)


def _ensure_file_exists() -> None:
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]\n", encoding="utf-8")


def _write_backup(raw_content: str) -> None:
    try:
        BACKUP_FILE.write_text(raw_content, encoding="utf-8")
    except OSError as exc:
        LOGGER.exception("Failed to write tasks backup to %s: %s", BACKUP_FILE, exc)


def _backup_existing_tasks_file() -> None:
    if not TASKS_FILE.exists():
        return
    try:
        _write_backup(TASKS_FILE.read_text(encoding="utf-8"))
    except OSError as exc:
        LOGGER.exception("Failed to read tasks file for backup: %s", exc)


def _recover_corrupted_file(raw_content: str, reason: str) -> list[dict[str, Any]]:
    LOGGER.error("Detected corrupted tasks.json: %s. Recovering with empty list.", reason)
    _write_backup(raw_content)
    save_tasks([])
    return []


def _normalize_task(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    task_id = item.get("id")
    text = item.get("text")
    if not isinstance(task_id, int):
        return None
    if not isinstance(text, str):
        return None

    status = item.get("status")
    created_at = item.get("created_at")
    completed_at = item.get("completed_at")

    if status == LEGACY_STATUS_COMPLETED:
        normalized_status = STATUS_ARCHIVED
    elif isinstance(status, str) and status in VALID_STATUSES:
        normalized_status = status
    else:
        done = item.get("done")
        if not isinstance(done, bool):
            return None
        normalized_status = STATUS_ARCHIVED if done else STATUS_ACTIVE

    if not isinstance(created_at, str):
        created_at = ""

    if normalized_status != STATUS_ARCHIVED:
        completed_at = None
    elif isinstance(completed_at, str):
        pass
    elif created_at:
        completed_at = created_at
    else:
        completed_at = ""

    return {
        "id": task_id,
        "text": text,
        "status": normalized_status,
        "created_at": created_at,
        "completed_at": completed_at,
    }


def load_tasks() -> list[dict[str, Any]]:
    _ensure_file_exists()

    raw_content = TASKS_FILE.read_text(encoding="utf-8")
    content = raw_content.strip()
    if not content:
        return []

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return _recover_corrupted_file(raw_content, "invalid JSON")

    if not isinstance(data, list):
        return _recover_corrupted_file(raw_content, "root is not a JSON array")

    normalized: list[dict[str, Any]] = []
    migration_needed = False
    for item in data:
        task = _normalize_task(item)
        if task is not None:
            normalized.append(task)
            if task != item:
                migration_needed = True
        else:
            migration_needed = True

    if migration_needed:
        save_tasks(normalized)

    return normalized


def save_tasks(tasks: list[dict[str, Any]]) -> None:
    _backup_existing_tasks_file()

    normalized = []
    for item in tasks:
        task = _normalize_task(item)
        if task is not None:
            normalized.append(task)

    TASKS_FILE.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
