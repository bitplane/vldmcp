"""Configuration management for vldmcp using Pydantic models and TOML."""

import tomllib
import tomli_w

from . import paths
from .models.config import Config, RuntimeConfig, NativeConfig, PodmanConfig


class ConfigManager:
    """Configuration manager for vldmcp."""

    def __init__(self):
        self._config: Config | None = None
        self._config_file = paths.config_dir() / "config.toml"

    def _load(self) -> Config:
        """Load configuration from TOML file."""
        if self._config is not None:
            return self._config

        if self._config_file.exists():
            try:
                with open(self._config_file, "rb") as f:
                    data = tomllib.load(f)
                self._config = Config.model_validate(data)
            except (tomllib.TOMLDecodeError, OSError, ValueError) as e:
                # If config is invalid, fall back to defaults and save
                print(f"Warning: Invalid config file {self._config_file}: {e}")
                print("Using default configuration")
                self._config = Config()
                self._save()
        else:
            # Create default config
            self._config = Config()
            self._save()

        return self._config

    def _save(self) -> None:
        """Save configuration to TOML file."""
        if self._config is None:
            return

        self._config_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save as TOML
        config_dict = self._config.model_dump(exclude_defaults=False, exclude_none=True)
        with open(self._config_file, "wb") as f:
            tomli_w.dump(config_dict, f)

    def get(self) -> Config:
        """Get the current configuration."""
        return self._load()

    def set_runtime_type(self, runtime_type: str) -> None:
        """Set the runtime type and save configuration."""
        config = self._load()

        # Create new runtime config based on type
        if runtime_type == "native":
            config.runtime = NativeConfig()
        elif runtime_type == "podman":
            config.runtime = PodmanConfig()
        else:
            config.runtime = RuntimeConfig(type=runtime_type)

        self._save()

    def reload(self) -> Config:
        """Force reload configuration from file."""
        self._config = None
        return self._load()


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the current configuration."""
    return config_manager.get()


def set_runtime_type(runtime_type: str) -> None:
    """Set the runtime type in configuration."""
    config_manager.set_runtime_type(runtime_type)
