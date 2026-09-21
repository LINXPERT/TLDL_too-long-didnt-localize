"""
test_tldl.py

Quick unit tests for TLDL's core checks. Run with:
    python -m unittest test_tldl.py
"""

import unittest
from tldl import (
    check_missing_keys,
    check_orphaned_keys,
    check_placeholder_mismatches,
    check_length_overflow,
    get_placeholders,
)


SAMPLE_DATA = {
    "en": {
        "greeting": "Hello, {name}!",
        "quit": "Quit",
        "score": "Score: {points}",
    },
    "fr": {
        "greeting": "Bonjour, {name} !",
        # "quit" is missing on purpose
        "score": "Score : ",  # placeholder dropped on purpose
        "leftover_key": "Ancien texte",  # orphaned key on purpose
    },
    "es": {
        "greeting": "This translated string is way way way way longer than the original one",
        "quit": "Salir",
        "score": "Puntuación: {points}",
    },
}


class TestPlaceholders(unittest.TestCase):
    def test_finds_single_placeholder(self):
        self.assertEqual(get_placeholders("Hello {name}"), {"{name}"})

    def test_finds_multiple_placeholders(self):
        self.assertEqual(
            get_placeholders("{greeting}, {name}! You have {count} items."),
            {"{greeting}", "{name}", "{count}"},
        )

    def test_no_placeholders(self):
        self.assertEqual(get_placeholders("Plain text."), set())


class TestMissingKeys(unittest.TestCase):
    def test_detects_missing_key(self):
        missing = check_missing_keys(SAMPLE_DATA, "en")
        self.assertIn("quit", missing["fr"])

    def test_no_false_positive(self):
        missing = check_missing_keys(SAMPLE_DATA, "en")
        self.assertNotIn("greeting", missing["fr"])
        self.assertNotIn("quit", missing.get("es", []))


class TestOrphanedKeys(unittest.TestCase):
    def test_detects_orphaned_key(self):
        orphaned = check_orphaned_keys(SAMPLE_DATA, "en")
        self.assertIn("leftover_key", orphaned["fr"])

    def test_no_orphans_when_clean(self):
        orphaned = check_orphaned_keys(SAMPLE_DATA, "en")
        self.assertEqual(orphaned.get("es", []), [])


class TestPlaceholderMismatches(unittest.TestCase):
    def test_detects_dropped_placeholder(self):
        mismatches = check_placeholder_mismatches(SAMPLE_DATA, "en")
        keys_flagged = [m[0] for m in mismatches["fr"]]
        self.assertIn("score", keys_flagged)

    def test_no_false_positive_when_matching(self):
        mismatches = check_placeholder_mismatches(SAMPLE_DATA, "en")
        keys_flagged = [m[0] for m in mismatches.get("es", [])]
        self.assertNotIn("score", keys_flagged)


class TestLengthOverflow(unittest.TestCase):
    def test_detects_overflow(self):
        overflow = check_length_overflow(SAMPLE_DATA, "en", max_ratio=1.4)
        keys_flagged = [o[0] for o in overflow["es"]]
        self.assertIn("greeting", keys_flagged)

    def test_no_false_positive_within_ratio(self):
        overflow = check_length_overflow(SAMPLE_DATA, "en", max_ratio=1.4)
        keys_flagged = [o[0] for o in overflow.get("fr", [])]
        self.assertNotIn("greeting", keys_flagged)


if __name__ == "__main__":
    unittest.main()
