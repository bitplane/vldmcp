"""Configuration service for vldmcp."""

import tomllib
import tomli_w
from pathlib import Path

from .. import Service
from ...models.config import Config, PlatformConfig, NativeConfig, PodmanConfig


class ConfigService(Service):
    """Service that manages vldmcp configuration."""

    def __init__(self, files_service):
        super().__init__()
        self._files = files_service
        self._config: Config | None = None

    def _config_path(self) -> Path:
        """Get config file path from files service."""
        return self._files.config_dir() / "config.toml"

    def start(self):
        """Load configuration on start."""
        self.load()
        self._running = True

    def stop(self):
        """Save configuration on stop."""
        if self._config:
            self.save()
        self._running = False

    def load(self) -> Config:
        """Load configuration from disk.

        Returns:
            Loaded configuration object
        """
        if self._config is not None:
            return self._config

        config_path = self._config_path()
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    data = tomllib.load(f)
                self._config = Config.model_validate(data)
            except (tomllib.TOMLDecodeError, OSError, ValueError) as e:
                # If config is invalid, fall back to defaults but don't save
                print(f"Warning: Invalid config file {config_path}: {e}")
                print("Using default configuration")
                self._config = Config()
        else:
            # Use default config but don't auto-create file
            self._config = Config()

        return self._config

    def save(self) -> None:
        """Save current configuration to disk."""
        if self._config is None:
            return

        config_path = self._config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save as TOML
        config_dict = self._config.model_dump(mode="json", exclude_defaults=False)
        with open(config_path, "wb") as f:
            tomli_w.dump(config_dict, f)

    def get(self) -> Config:
        """Get current configuration.

        Returns:
            Current configuration object
        """
        if not self._config:
            self.load()
        return self._config

    def set_platform_type(self, platform_type: str) -> None:
        """Set the platform type in configuration.

        Args:
            platform_type: Platform type to set (native, podman, etc)
        """
        config = self.get()

        # Create new platform config based on type
        if platform_type == "native":
            config.platform = NativeConfig()
        elif platform_type == "podman":
            config.platform = PodmanConfig()
        else:
            config.platform = PlatformConfig(type=platform_type)

        self.save()

    def update(self, **kwargs) -> None:
        """Update configuration values.

        Args:
            **kwargs: Configuration values to update
        """
        if not self._config:
            self.load()

        # Update config with new values
        for key, value in kwargs.items():
            setattr(self._config, key, value)

        self.save()
