"""Persistent dictionary that automatically saves to storage."""

import tomllib
import tomli_w


class PersistentDict:
    """Dictionary that persists to storage backend."""

    def __init__(self, storage, file_path: str):
        """Initialize persistent dict.

        Args:
            storage: Storage service for file operations
            file_path: Relative path for the config file (e.g. "config.toml")
        """
        self.storage = storage
        self.file_path = file_path
        self.data = {}
        self._loaded = False

    def _ensure_loaded(self):
        """Ensure data is loaded from storage."""
        if not self._loaded:
            self.load()

    def load(self):
        """Load data from storage."""
        config_path = self.storage.config_dir() / self.file_path
        if config_path.exists():
            with open(config_path, "rb") as f:
                self.data = tomllib.load(f)
        else:
            self.data = {}
        self._loaded = True

    def save(self):
        """Save data to storage."""
        config_path = self.storage.config_dir() / self.file_path
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "wb") as f:
            tomli_w.dump(self.data, f)

    # Dict interface
    def __getitem__(self, key):
        self._ensure_loaded()
        return self.data[key]

    def __setitem__(self, key, value):
        self._ensure_loaded()
        self.data[key] = value
        self.save()  # Auto-save on update

    def __delitem__(self, key):
        self._ensure_loaded()
        del self.data[key]
        self.save()  # Auto-save on delete

    def __contains__(self, key):
        self._ensure_loaded()
        return key in self.data

    def __iter__(self):
        self._ensure_loaded()
        return iter(self.data)

    def __len__(self):
        self._ensure_loaded()
        return len(self.data)

    def keys(self):
        self._ensure_loaded()
        return self.data.keys()

    def values(self):
        self._ensure_loaded()
        return self.data.values()

    def items(self):
        self._ensure_loaded()
        return self.data.items()

    def get(self, key, default=None):
        self._ensure_loaded()
        return self.data.get(key, default)

    def clear(self):
        self._ensure_loaded()
        self.data.clear()
        self.save()  # Auto-save on clear
