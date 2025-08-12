"""Pretty print JSON objects in a compact format."""


def pretty_print(obj: dict | list, prefix: str = "") -> list[str]:
    """Pretty print a JSON object with dot notation for nested keys.

    Args:
        obj: JSON-like object to pretty print
        prefix: Current key prefix for nested objects

    Returns:
        List of formatted strings
    """
    result = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.extend(pretty_print(value, new_prefix))
            else:
                result.append(f"{new_prefix}: {format_value(value)}")
    elif isinstance(obj, list):
        for item in obj:
            result.extend(pretty_print(item, prefix))
    else:
        if prefix:
            result.append(f"{prefix}: {format_value(obj)}")

    return result


def format_value(value) -> str:
    """Format a value for pretty printing.

    Args:
        value: Value to format

    Returns:
        Formatted string
    """
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    elif isinstance(value, int) and value > 255:
        return str(value)
    else:
        return str(value)


def pprint(obj: dict | list) -> None:
    """Print a JSON object in pretty format."""
    for line in pretty_print(obj):
        print(line)
