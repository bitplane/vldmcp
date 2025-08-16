"""Main configuration model."""

from typing import Union

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .daemon import DaemonConfig
from .platform import PlatformConfig, NativeConfig, PodmanConfig


class Config(BaseSettings):
    """Main vldmcp configuration."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_prefix="VLDMCP_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    platform: Union[PlatformConfig, NativeConfig, PodmanConfig] = Field(
        default_factory=lambda: PlatformConfig(), description="Platform configuration"
    )
    daemon: DaemonConfig = Field(default_factory=DaemonConfig, description="Daemon configuration")

    @model_validator(mode="before")
    @classmethod
    def validate_platform_type(cls, values):
        """Validate and convert platform config based on type."""
        if isinstance(values, dict) and "platform" in values:
            platform_data = values["platform"]
            if isinstance(platform_data, dict):
                platform_type = platform_data.get("type", "guess")

                # Convert to appropriate config type
                if platform_type == "native":
                    values["platform"] = NativeConfig(**platform_data)
                elif platform_type == "podman":
                    values["platform"] = PodmanConfig(**platform_data)
                # else keep as base PlatformConfig for "guess" type

        return values
