from datetime import datetime

from django.test import TestCase

from .utils import sanitize_cell, sanitize_row


class CSVSanitizationTests(TestCase):
    def test_sanitize_strings_pass_through(self):
        """Safe strings should not be modified."""
        self.assertEqual(sanitize_cell("Normal Test"), "Normal Test")
        self.assertEqual(sanitize_cell("123 Safe"), "123 Safe")

    def test_dangerous_prefixes(self):
        """Strings starting with =, +, -, @, \t, or \r must be with a quote."""

        dangerous_values = [
            "=SUM(A1:B1)",
            "+1+1",
            "-1+1",
            "@cmd|'/C calc'!A0",
            "\tTabbed content",
            "\rCarriage return",
        ]

        for val in dangerous_values:
            with self.subTest(value=val):
                self.assertEqual(sanitize_cell(val), f"'{val}")

    def test_lstrip_behavior_on_dangerous_prefixes(self):
        """Leading whitespace should not bypass the prefix check (e.g., '  =cmd')."""
        self.assertEqual(sanitize_cell("   =cmd"), "'   =cmd")
        self.assertEqual(sanitize_cell("\n\n+SUM(1,2)"), "'\n\n+SUM(1,2)")

    def test_non_string_passthrough(self):
        """Non-string types (int, float, None, bool, datetime) should pass untouched."""
        self.assertEqual(sanitize_cell(123), 123)
        self.assertEqual(sanitize_cell(-5), -5)
        self.assertEqual(sanitize_cell(-12.34), -12.34)
        self.assertIsNone(sanitize_cell(None))
        self.assertEqual(sanitize_cell(True), True)

        now = datetime.now()
        self.assertEqual(sanitize_cell(now), now)

    def test_negative_numbers_as_strings(self):
        """Tradeoff check: Negative numbers formatted as strings get prepended."""
        self.assertEqual(sanitize_cell("-500"), "'-500")

    def test_sanitize_row(self):
        """Ensure sanitize_row correctly maps sanitize_cell across an iterable."""
        row = [1, "=malicious", "safe", "-100", None]
        expected = [1, "'=malicious", "safe", "'-100", None]
        self.assertEqual(sanitize_row(row), expected)
