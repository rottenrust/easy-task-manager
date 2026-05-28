import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from task_manager import service
from task_manager import storage


class TaskServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self._old_tasks_file = storage.TASKS_FILE
        storage.TASKS_FILE = Path(self._tmpdir.name) / "tasks.json"

    def tearDown(self) -> None:
        storage.TASKS_FILE = self._old_tasks_file
        self._tmpdir.cleanup()

    def test_add_task_creates_active_task(self) -> None:
        task = service.add_task("Buy milk")

        self.assertEqual(task["id"], 1)
        self.assertEqual(task["text"], "Buy milk")
        self.assertEqual(task["status"], storage.STATUS_ACTIVE)
        self.assertIsNone(task["completed_at"])

        persisted = storage.load_tasks()
        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0]["text"], "Buy milk")

    def test_list_active_tasks_excludes_archived(self) -> None:
        first = service.add_task("Active task")
        second = service.add_task("Will be archived")

        ok, status = service.archive_task(second["id"])
        self.assertTrue(ok)
        self.assertEqual(status, "archived")

        active = service.list_active_tasks()
        self.assertEqual([task["id"] for task in active], [first["id"]])

    def test_archive_task_marks_task_as_archived(self) -> None:
        task = service.add_task("Finish report")

        ok, status = service.archive_task(task["id"])
        self.assertTrue(ok)
        self.assertEqual(status, "archived")

        persisted = storage.load_tasks()
        self.assertEqual(persisted[0]["status"], storage.STATUS_ARCHIVED)
        self.assertIsInstance(persisted[0]["completed_at"], str)
        self.assertNotEqual(persisted[0]["completed_at"], "")

    def test_list_archived_tasks_returns_only_archived(self) -> None:
        active_task = service.add_task("Active task")
        archived_task = service.add_task("Archived task")
        service.archive_task(archived_task["id"])

        archived = service.list_archived_tasks()
        self.assertEqual([task["id"] for task in archived], [archived_task["id"]])
        self.assertNotEqual(archived[0]["id"], active_task["id"])

    def test_archive_task_for_missing_task(self) -> None:
        ok, status = service.archive_task(999)

        self.assertFalse(ok)
        self.assertEqual(status, "not_found")

    def test_restore_task_by_id_restores_archived_task(self) -> None:
        task = service.add_task("Restore me")
        service.archive_task(task["id"])

        restored, status = service.restore_task(task["id"])

        self.assertEqual(status, "restored")
        self.assertIsNotNone(restored)
        self.assertEqual(restored["status"], storage.STATUS_ACTIVE)
        self.assertIsNone(restored["completed_at"])

    def test_restore_task_by_id_for_missing_task(self) -> None:
        restored, status = service.restore_task(321)

        self.assertIsNone(restored)
        self.assertEqual(status, "not_found")

    def test_restore_task_by_id_for_active_task(self) -> None:
        task = service.add_task("Still active")

        restored, status = service.restore_task(task["id"])

        self.assertIsNone(restored)
        self.assertEqual(status, "not_archived")

    def test_restore_last_archived_task_restores_latest_archived(self) -> None:
        first = service.add_task("First")
        second = service.add_task("Second")
        service.archive_task(first["id"])
        service.archive_task(second["id"])

        restored, status = service.restore_last_archived_task()

        self.assertEqual(status, "restored")
        self.assertIsNotNone(restored)
        self.assertEqual(restored["id"], second["id"])
        self.assertEqual(restored["status"], storage.STATUS_ACTIVE)
        self.assertIsNone(restored["completed_at"])

    def test_restore_last_archived_task_when_archive_empty(self) -> None:
        restored, status = service.restore_last_archived_task()

        self.assertIsNone(restored)
        self.assertEqual(status, "archive_empty")

    def test_clear_archive_removes_only_archived_tasks(self) -> None:
        active = service.add_task("Active")
        archived = service.add_task("Archived")
        service.archive_task(archived["id"])

        removed = service.clear_archive()

        self.assertEqual(removed, 1)
        remaining = service.list_active_tasks()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["id"], active["id"])

    def test_clear_archive_returns_zero_when_archive_already_empty(self) -> None:
        service.add_task("Only active")

        removed = service.clear_archive()

        self.assertEqual(removed, 0)


if __name__ == "__main__":
    unittest.main()
