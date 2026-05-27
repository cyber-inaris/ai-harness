import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts import provider_bindings


class ProviderBindingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "provider-bindings.sqlite"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_record_and_exclude_successful_binding(self) -> None:
        provider_bindings.init_db(self.db_path)
        provider_bindings.record_binding(
            self.db_path,
            {
                "provider": "freemodel",
                "provider_account_ref": "wgsr7b2t7@mozmail.com",
                "telegram_id": "7214827159",
                "start_code": "abc123",
                "start_link": "https://t.me/FreeModelDevBot?start=abc123",
                "status": "success",
                "bot_response_status": "success",
                "bot_response_text": "Account bound successfully.",
                "ss_panel_response_json": json.dumps({"ok": True}),
                "executor": "codex-mac",
            },
        )

        self.assertEqual(
            provider_bindings.exclude_telegram_ids(self.db_path, "freemodel"),
            ["7214827159"],
        )

    def test_exclude_policy_includes_pending_failed_and_send_failed(self) -> None:
        provider_bindings.init_db(self.db_path)
        for status, telegram_id in [
            ("pending", "1"),
            ("success", "2"),
            ("failed", "3"),
            ("send_failed", "4"),
            ("expired", "5"),
            ("unknown", "6"),
        ]:
            provider_bindings.record_binding(
                self.db_path,
                {
                    "provider": "freemodel",
                    "telegram_id": telegram_id,
                    "start_code": f"code-{telegram_id}",
                    "start_link": f"https://t.me/FreeModelDevBot?start=code-{telegram_id}",
                    "status": status,
                },
            )

        self.assertEqual(
            provider_bindings.exclude_telegram_ids(self.db_path, "freemodel"),
            ["1", "2", "3", "4"],
        )

    def test_classify_sspanel_result(self) -> None:
        self.assertEqual(
            provider_bindings.classify_sspanel_result(
                {
                    "telegramId": "1",
                    "botResponseStatus": "unknown",
                    "botResponseText": "⌛️ This binding link has expired. Please generate a new one on the website.",
                }
            ),
            "expired",
        )
        self.assertEqual(
            provider_bindings.classify_sspanel_result(
                {
                    "telegramId": "2",
                    "error": "sendDirectMessage returned false",
                    "messageResults": [{"error": "sendDirectMessage returned false"}],
                }
            ),
            "send_failed",
        )
        self.assertEqual(
            provider_bindings.classify_sspanel_result(
                {
                    "telegramId": "3",
                    "botResponseText": "This Telegram account is already bound to a different account.",
                }
            ),
            "failed",
        )
        self.assertEqual(
            provider_bindings.classify_sspanel_result(
                {
                    "telegramId": "4",
                    "botResponseStatus": "success",
                    "botResponseText": "Account bound successfully. You can return to the website.",
                }
            ),
            "success",
        )

    def test_success_unique_index_allows_only_one_success_per_provider_account(self) -> None:
        provider_bindings.init_db(self.db_path)
        record = {
            "provider": "freemodel",
            "telegram_id": "7214827159",
            "start_code": "first",
            "start_link": "https://t.me/FreeModelDevBot?start=first",
            "status": "success",
        }
        provider_bindings.record_binding(self.db_path, record)
        with self.assertRaises(sqlite3.IntegrityError):
            provider_bindings.record_binding(
                self.db_path,
                {
                    **record,
                    "start_code": "second",
                    "start_link": "https://t.me/FreeModelDevBot?start=second",
                },
            )


if __name__ == "__main__":
    unittest.main()
