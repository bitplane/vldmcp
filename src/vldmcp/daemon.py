"""Direct server entry point.

This allows running the server directly with: python -m vldmcp.server
This bypasses the CLI and starts the server immediately.
"""

import sys
import os


def main():
    """Main entry point for the server module."""
    # This will eventually be the actual server implementation
    # For now, it calls the CLI's start command directly

    # Ensure XDG directories exist
    from . import paths

    paths.create_directories()

    # Ensure user key exists
    from . import crypto

    crypto.ensure_user_key()

    # Write PID file
    pid_file = paths.pid_file_path()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))

    try:
        print(f"vldmcp server starting (PID: {os.getpid()})...")
        print(f"Config: {paths.config_dir()}")
        print(f"Data: {paths.data_dir()}")
        print(f"State: {paths.state_dir()}")
        print(f"Cache: {paths.cache_dir()}")
        print("Server would run here (not yet implemented)")

        # In the future, this would start the actual server
        # For now, just simulate
        import time

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    finally:
        # Clean up PID file
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(0)


if __name__ == "__main__":
    main()
