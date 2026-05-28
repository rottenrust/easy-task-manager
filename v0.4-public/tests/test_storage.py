import tempfile
import unittest
from pathlib import Path

from task_manager import storage


class StorageReliabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self._old_tasks_file = storage.TASKS_FILE
        self._old_backup_file = storage.BACKUP_FILE
        storage.TASKS_FILE = Path(self._tmpdir.name) / "tasks.json"
        storage.BACKUP_FILE = storage.TASKS_FILE.with_name("tasks.json.bak")

    def tearDown(self) -> None:
        storage.TASKS_FILE = self._old_tasks_file
        storage.BACKUP_FILE = self._old_backup_file

    def test_load_tasks_recovers_corrupted_json_and_writes_backup(self) -> None:
        storage.TASKS_FILE.write_text("{bad json", encoding="utf-8")

        tasks = storage.load_tasks()

        self.assertEqual(tasks, [])
        self.assertEqual(storage.TASKS_FILE.read_text(encoding="utf-8"), "[]\n")
        self.assertEqual(storage.BACKUP_FILE.read_text(encoding="utf-8"), "{bad json")

    def test_save_tasks_creates_backup_before_write(self) -> None:
        storage.TASKS_FILE.write_text('[{"id": 1, "text": "old", "status": "active", "created_at": "", "completed_at": null}]\n', encoding="utf-8")

        storage.save_tasks(
            [{"id": 2, "text": "new", "status": "active", "created_at": "", "completed_at": None}]
        )

        self.assertIn('"id": 1', storage.BACKUP_FILE.read_text(encoding="utf-8"))
        self.assertIn('"id": 2', storage.TASKS_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
