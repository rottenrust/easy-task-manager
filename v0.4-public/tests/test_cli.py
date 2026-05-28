import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from task_manager import cli


class CLITests(unittest.TestCase):
    def test_build_parser_contains_telegram_command(self) -> None:
        parser = cli.build_parser()

        args = parser.parse_args(["telegram"])

        self.assertEqual(args.command, "telegram")

    @patch("task_manager.cli.run_long_polling")
    def test_cmd_telegram_handles_keyboard_interrupt(self, polling_mock) -> None:
        polling_mock.side_effect = KeyboardInterrupt()
        output = io.StringIO()

        with redirect_stdout(output):
            cli.cmd_telegram()

        self.assertIn("Bot stopped.", output.getvalue())

    @patch("task_manager.cli.run_long_polling")
    def test_cmd_telegram_handles_runtime_error(self, polling_mock) -> None:
        polling_mock.side_effect = ValueError("missing token")
        output = io.StringIO()

        with redirect_stdout(output):
            cli.cmd_telegram()

        self.assertIn("Telegram polling failed: missing token", output.getvalue())


if __name__ == "__main__":
    unittest.main()
