"""Main configuration model."""

from typing import Union

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .daemon import DaemonConfig
from .runtime import RuntimeConfig, NativeConfig, PodmanConfig


class Config(BaseSettings):
    """Main vldmcp configuration."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_prefix="VLDMCP_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    runtime: Union[RuntimeConfig, NativeConfig, PodmanConfig] = Field(
        default_factory=lambda: RuntimeConfig(), description="Runtime configuration"
    )
    daemon: DaemonConfig = Field(default_factory=DaemonConfig, description="Daemon configuration")

    @model_validator(mode="before")
    @classmethod
    def validate_runtime_type(cls, values):
        """Validate and convert runtime config based on type."""
        if isinstance(values, dict) and "runtime" in values:
            runtime_data = values["runtime"]
            if isinstance(runtime_data, dict):
                runtime_type = runtime_data.get("type", "guess")

                # Convert to appropriate config type
                if runtime_type == "native":
                    values["runtime"] = NativeConfig(**runtime_data)
                elif runtime_type == "podman":
                    values["runtime"] = PodmanConfig(**runtime_data)
                # else keep as base RuntimeConfig for "guess" type

        return values
