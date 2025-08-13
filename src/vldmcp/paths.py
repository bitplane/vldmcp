"""XDG-compliant path management for vldmcp.

This module provides transparent access to XDG Base Directory compliant paths,
falling back to sensible defaults when XDG environment variables are not set.
"""

import os
from pathlib import Path


def config_dir() -> Path:
    """Get the configuration directory.

    Returns $XDG_CONFIG_HOME/vldmcp or ~/.config/vldmcp if XDG_CONFIG_HOME is not set.
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "vldmcp"
    return Path.home() / ".config" / "vldmcp"


def data_dir() -> Path:
    """Get the user data directory.

    Returns $XDG_DATA_HOME/vldmcp or ~/.local/share/vldmcp if XDG_DATA_HOME is not set.
    """
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "vldmcp"
    return Path.home() / ".local" / "share" / "vldmcp"


def state_dir() -> Path:
    """Get the state directory.

    Returns $XDG_STATE_HOME/vldmcp or ~/.local/state/vldmcp if XDG_STATE_HOME is not set.
    """
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state) / "vldmcp"
    return Path.home() / ".local" / "state" / "vldmcp"


def cache_dir() -> Path:
    """Get the cache directory.

    Returns $XDG_CACHE_HOME/vldmcp or ~/.cache/vldmcp if XDG_CACHE_HOME is not set.
    """
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / "vldmcp"
    return Path.home() / ".cache" / "vldmcp"


def runtime_dir() -> Path:
    """Get the runtime directory.

    Returns $XDG_RUNTIME_DIR/vldmcp or /tmp/vldmcp-$USER if XDG_RUNTIME_DIR is not set.
    """
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime:
        return Path(xdg_runtime) / "vldmcp"
    user = os.environ.get("USER", "unknown")
    return Path(f"/tmp/vldmcp-{user}")


def user_key_path() -> Path:
    """Get the path to the user identity key file."""
    return data_dir() / "keys" / "user.key"


def node_dir(node_id: str) -> Path:
    """Get the directory for a specific node's data."""
    return state_dir() / "nodes" / node_id


def node_key_path(node_id: str) -> Path:
    """Get the path to a specific node's key file."""
    return node_dir(node_id) / "key"


def repos_dir() -> Path:
    """Get the directory where git repositories are cached."""
    return cache_dir() / "src"


def build_dir() -> Path:
    """Get the directory where builds are cached."""
    return cache_dir() / "build"


def install_dir() -> Path:
    """Get the directory where application install data is stored."""
    return data_dir() / "install"


def www_dir() -> Path:
    """Get the directory for serving static files and models."""
    return data_dir() / "www"


def pid_file_path() -> Path:
    """Get the path to the server PID file."""
    return runtime_dir() / "vldmcp.pid"


def create_directories() -> None:
    """Create all necessary directories with appropriate permissions."""
    # Create config directory
    config_dir().mkdir(parents=True, exist_ok=True)

    # Create data directory and keys subdirectory with secure permissions
    keys_dir = data_dir() / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    # Create state directory with secure permissions
    state_dir().mkdir(parents=True, exist_ok=True, mode=0o700)

    # Create cache directories
    cache_dir().mkdir(parents=True, exist_ok=True)
    repos_dir().mkdir(parents=True, exist_ok=True)
    build_dir().mkdir(parents=True, exist_ok=True)

    # Create install directory
    install_dir().mkdir(parents=True, exist_ok=True)

    # Create www directory and subdirectories
    www = www_dir()
    www.mkdir(parents=True, exist_ok=True)
    (www / "models").mkdir(exist_ok=True)
    (www / "assets").mkdir(exist_ok=True)
    (www / "uploads").mkdir(exist_ok=True)
    (www / "generated").mkdir(exist_ok=True)

    # Create runtime directory with secure permissions
    runtime_dir().mkdir(parents=True, exist_ok=True, mode=0o700)


def ensure_secure_permissions() -> None:
    """Ensure all sensitive directories and files have correct permissions."""
    # Secure the keys directory
    keys_dir = data_dir() / "keys"
    if keys_dir.exists():
        keys_dir.chmod(0o700)

        # Secure the user key file if it exists
        user_key = user_key_path()
        if user_key.exists():
            user_key.chmod(0o600)

    # Secure the state directory
    if state_dir().exists():
        state_dir().chmod(0o700)

        # Secure all node directories and key files
        nodes_dir = state_dir() / "nodes"
        if nodes_dir.exists():
            for node_path in nodes_dir.iterdir():
                if node_path.is_dir():
                    node_path.chmod(0o700)
                    key_file = node_path / "key"
                    if key_file.exists():
                        key_file.chmod(0o600)

    # Secure the runtime directory
    if runtime_dir().exists():
        runtime_dir().chmod(0o700)
