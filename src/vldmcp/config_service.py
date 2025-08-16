"""Configuration service for vldmcp."""

from .service import Service
from .models.config import Config
from . import paths


class ConfigService(Service):
    """Service that manages vldmcp configuration."""

    def __init__(self):
        super().__init__()
        self._config = None
        self._config_path = paths.config_dir() / "config.toml"

    @classmethod
    def name(cls) -> str:
        return "config"

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
        if self._config_path.exists():
            import toml

            config_data = toml.load(self._config_path)
            self._config = Config(**config_data)
        else:
            # Create default config
            self._config = Config()
        return self._config

    def save(self) -> None:
        """Save current configuration to disk."""
        if not self._config:
            return

        # Ensure config directory exists
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to TOML
        import toml

        config_data = self._config.model_dump(exclude_defaults=True)
        with open(self._config_path, "w") as f:
            toml.dump(config_data, f)

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
        if not self._config:
            self.load()
        self._config.platform.type = platform_type
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
            if hasattr(self._config, key):
                setattr(self._config, key, value)

        self.save()
