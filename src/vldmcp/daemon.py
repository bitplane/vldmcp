"""Direct server entry point.

This allows running the server directly with: python -m vldmcp.server
This bypasses the CLI and starts the server immediately.
"""

import os
import sys
import time

from . import crypto, paths


def main():
    """Main entry point for the server module."""
    # Ensure XDG directories exist
    paths.create_directories()

    # Ensure user key exists
    crypto.ensure_user_key()

    # Write PID file (inside container this goes to /var/run, outside it's managed by deployment)
    pid_file = paths.pid_file_path()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))

    try:
        print(f"vldmcp server starting (PID: {os.getpid()})...")
        print(f"Config: {paths.config_dir()}")
        print(f"Data: {paths.data_dir()}")
        print(f"State: {paths.state_dir()}")
        print(f"Cache: {paths.cache_dir()}")

        # Server implementation placeholder - replace with actual MCP server implementation
        print("Server daemon running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    finally:
        # Clean up PID file (inside container)
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(0)


if __name__ == "__main__":
    main()
