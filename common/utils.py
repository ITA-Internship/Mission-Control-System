class EchoBuffer:
    def write(self, value):
        return value


DANGEROUS_PREFIXES = ("=", "+", "-", "@", "|", "\t", "\r")


def sanitize_cell(value):
    """
    Sanitizes string values to prevent CSV/Formula Injection.

    NOTE ON NEGATIVE NUMBERS (TRADEOFF):
    This implementation include '-' in DANGEROUS_PREFIXES to prevent csv injection.
    Raw numeric types bypass this check and export correctly as numbers (e.g., -5).
    However, if a negative number is passed as a string, it will be prepended
    with a quote ("'-5") and treated as text by spreadsheet software.
    Ensure numeric values are passed as int/float, not str, when generating CSVs.
    """

    if isinstance(value, str) and value.lstrip(" \n").startswith(DANGEROUS_PREFIXES):
        return f"'{value}"
    return value


def sanitize_row(row):
    return [sanitize_cell(cell) for cell in row]
