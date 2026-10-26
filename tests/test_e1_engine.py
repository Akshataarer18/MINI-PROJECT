import unittest
from e1_engine import ConcurrencyEngine


class TestConcurrencyEngine(unittest.TestCase):
    def test_authorized_edit_is_accepted_and_version_increments(self):
        engine = ConcurrencyEngine("Initial")
        result = engine.apply_edit("Alice", "Updated", True, 1)
        self.assertEqual(result["status"], "ACCEPTED")
        self.assertEqual(engine.content, "Updated")
        self.assertEqual(engine.version, 2)

    def test_stale_version_is_a_conflict_and_does_not_overwrite(self):
        engine = ConcurrencyEngine("Initial")
        engine.apply_edit("Alice", "First update", True, 1)
        result = engine.apply_edit("Bob", "Stale update", True, 1)
        self.assertEqual(result["status"], "CONFLICT")
        self.assertEqual(result["current_version"], 2)
        self.assertEqual(engine.content, "First update")

    def test_permission_denied(self):
        engine = ConcurrencyEngine("Initial")
        result = engine.apply_edit("Charlie", "Unauthorized", False, 1)
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(engine.content, "Initial")
        self.assertEqual(engine.version, 1)

    def test_invalid_username_is_rejected(self):
        engine = ConcurrencyEngine("Initial")
        result = engine.apply_edit(" ", "Updated", True, 1)
        self.assertEqual(result["status"], "REJECTED")

    def test_too_large_document_is_rejected(self):
        engine = ConcurrencyEngine("Initial")
        result = engine.apply_edit("Alice", "x" * 20001, True, 1)
        self.assertEqual(result["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
