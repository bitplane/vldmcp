"""Entry point for running vldmcp as a module.

This allows running with: python -m vldmcp
"""

from .cli import cli

if __name__ == "__main__":
    cli()
