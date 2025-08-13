"""Pretty printing utilities for vldmcp."""


def pprint_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "1.2G", "456M", "789K")
    """
    if size_bytes == 0:
        return "0B"

    units = ["B", "K", "M", "G", "T", "P"]
    size = float(size_bytes)
    for unit in units[:-1]:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}{units[-1]}"


def pprint_dict(obj: dict | list, prefix: str = "") -> None:
    """Pretty print a dictionary or list with dot notation for nested keys.

    Args:
        obj: Dictionary or list to pretty print
        prefix: Current key prefix for nested objects
    """
    result = _format_dict(obj, prefix)
    for line in result:
        print(line)


def _format_dict(obj: dict | list, prefix: str = "") -> list[str]:
    """Format a dictionary or list for pretty printing.

    Args:
        obj: Object to format
        prefix: Current key prefix for nested objects

    Returns:
        List of formatted strings
    """
    result = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.extend(_format_dict(value, new_prefix))
            elif isinstance(value, list):
                # Format lists inline
                result.append(f"{new_prefix}: {_format_value(value)}")
            else:
                result.append(f"{new_prefix}: {_format_value(value)}")
    elif isinstance(obj, list):
        for item in obj:
            result.extend(_format_dict(item, prefix))
    else:
        if prefix:
            result.append(f"{prefix}: {_format_value(obj)}")

    return result


def _format_value(value) -> str:
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
