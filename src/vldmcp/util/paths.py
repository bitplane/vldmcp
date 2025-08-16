"""XDG-compliant path utilities for vldmcp."""

import os
from pathlib import Path


class _PathsClass:
    """Standard paths for vldmcp following XDG Base Directory specification."""

    @property
    def _data_home(self):
        return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    @property
    def _config_home(self):
        return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    @property
    def _state_home(self):
        return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))

    @property
    def _cache_home(self):
        return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    @property
    def _runtime_dir(self):
        return Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/vldmcp-{os.environ.get('USER', 'unknown')}"))

    @property
    def DATA(self):
        return self._data_home / "vldmcp"

    @property
    def CONFIG(self):
        return self._config_home / "vldmcp"

    @property
    def STATE(self):
        return self._state_home / "vldmcp"

    @property
    def CACHE(self):
        return self._cache_home / "vldmcp"

    @property
    def RUNTIME(self):
        return self._runtime_dir / "vldmcp"

    @property
    def INSTALL(self):
        return self.DATA / "install"

    @property
    def KEYS(self):
        return self.DATA / "keys"

    @property
    def WWW(self):
        return self.DATA / "www"

    @property
    def REPOS(self):
        return self.CACHE / "src"

    @property
    def BUILD(self):
        return self.CACHE / "build"


# Create singleton instance
Paths = _PathsClass()
