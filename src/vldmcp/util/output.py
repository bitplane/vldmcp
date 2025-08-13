"""Output formatting utilities."""

import click


def output_nested_dict(d, prefix=""):
    """Output nested dictionary in tab-separated format."""
    for key, value in d.items():
        if isinstance(value, dict):
            # Nested dict - recurse with prefix
            new_prefix = f"{prefix}.{key}" if prefix else key
            output_nested_dict(value, new_prefix)
        else:
            # Leaf value - output as tab-separated
            full_key = f"{prefix}.{key}" if prefix else key
            if value and value != 0 and value != "0B":
                click.echo(f"{full_key}\t{value}")
