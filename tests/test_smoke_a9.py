"""A9 unit: checklist smoke chạy mock, không fail khi Ollama chết."""

from __future__ import annotations

import unittest

from tests.smoke_a9 import run_smoke


class TestSmokeA9(unittest.TestCase):
    def test_smoke_offline_no_tts(self) -> None:
        report = run_smoke(do_tts=False, user_text="Bật đèn")
        self.assertEqual(len(report.steps), 5)
        # Bước 1–3–5 phải pass với mock; 4 có thể skip
        by_n = {s.n: s for s in report.steps}
        self.assertEqual(by_n[1].status, "pass")
        self.assertEqual(by_n[2].status, "pass")
        self.assertEqual(by_n[3].status, "pass")
        self.assertIn(by_n[4].status, ("pass", "skip"))
        self.assertEqual(by_n[5].status, "pass")
        self.assertTrue(report.ok())


if __name__ == "__main__":
    unittest.main()
