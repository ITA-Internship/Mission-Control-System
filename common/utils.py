class EchoBuffer:
    def write(self, value):
        return value


DANGEROUS_PREFIXES = ("=", "+", "-", "@", "|")


def sanitize_cell(value):
    if isinstance(value, str):
        stripped_value = value.lstrip()

        if stripped_value.startswith(DANGEROUS_PREFIXES):
            return f"'{value}"

    return value


def sanitize_row(row):
    return [sanitize_cell(cell) for cell in row]
