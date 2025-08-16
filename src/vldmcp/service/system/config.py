"""Configuration service for vldmcp."""

from ..base import Service
from ...util.persistent_dict import PersistentDict
from ...models.config import Config


class ConfigService(Service):
    """Service that manages vldmcp configuration."""

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.data = PersistentDict(storage, "config.toml")

    def get_config(self) -> Config:
        """Get the full configuration as a Config object."""
        # Load raw dict and convert to Config model
        raw_data = dict(self.data.items()) if self.data else {}

        # Set defaults if empty
        if not raw_data:
            raw_data = {"platform": {"type": "guess"}}

        return Config.model_validate(raw_data)

    def save_config(self, config: Config):
        """Save a Config object to storage."""
        # Convert config to dict and update our data
        config_dict = config.model_dump()

        # Clear and update
        self.data.clear()
        for key, value in config_dict.items():
            self.data[key] = value
