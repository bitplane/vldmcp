"""Podman container runtime backend."""

import json
import shutil
import subprocess
from pathlib import Path

from ... import __version__
from ...models.disk_usage import DiskUsage
from .base import Platform


class PodmanPlatform(Platform):
    """Podman container platform backend."""

    def _get_podman_config(self):
        """Get podman-specific configuration values."""
        config = self.config.get_config()
        plat = config.platform
        return plat.image_name, plat.container_name

    def build(self, force: bool = False) -> bool:
        """Build container with podman."""
        base_dir = self.storage.install_dir() / "base"
        dockerfile = base_dir / "Dockerfile"

        if not dockerfile.exists():
            return False

        # Get config values
        image_name, _ = self._get_podman_config()

        # Build with version spec if we have a known version
        version_spec = f"=={__version__}" if __version__ != "unknown" else ""

        result = subprocess.run(
            [
                "podman",
                "build",
                "--build-arg",
                f"VERSION_SPEC={version_spec}",
                "-t",
                image_name,
                str(dockerfile.parent),
            ],
            capture_output=True,
        )
        return result.returncode == 0

    def status(self) -> str:
        """Check podman container status."""
        if not self.storage.config_dir().exists():
            return "not deployed"

        _, container_name = self._get_podman_config()
        result = subprocess.run(
            ["podman", "ps", "-a", "--filter", f"name={container_name}"], capture_output=True, text=True
        )
        if container_name in result.stdout:
            if "Up" in result.stdout:
                return "running"
            else:
                return "stopped"
        return "not found"

    def du(self) -> DiskUsage:
        """Get disk usage including container images and volumes.

        Returns:
            DiskUsage model with sizes in bytes by functional area including container storage
        """
        # Get base sizes from parent implementation
        usage = super().du()

        # Get container image sizes
        images_size = 0
        try:
            # Get all vldmcp-related images
            result = subprocess.run(
                ["podman", "images", "--format", "json", "--filter", "reference=vldmcp*"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                images = json.loads(result.stdout)
                for image in images:
                    if "Size" in image:
                        images_size += image["Size"]
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            pass

        # Get container volumes size - add to mcp.data
        volumes_size = 0
        try:
            # Get volumes used by vldmcp containers
            result = subprocess.run(
                ["podman", "volume", "ls", "--format", "json"], capture_output=True, text=True, check=True
            )
            if result.stdout:
                volumes = json.loads(result.stdout)
                for volume in volumes:
                    if "vldmcp" in volume.get("Name"):
                        # Get size of this volume
                        vol_result = subprocess.run(
                            ["podman", "volume", "inspect", volume["Name"]], capture_output=True, text=True, check=True
                        )
                        if vol_result.stdout:
                            vol_info = json.loads(vol_result.stdout)
                            if vol_info and "Mountpoint" in vol_info[0]:
                                mount = vol_info[0]["Mountpoint"]
                                # Get size of mountpoint
                                du_result = subprocess.run(
                                    ["du", "-sb", mount], capture_output=True, text=True, check=True
                                )
                                volumes_size += int(du_result.stdout.split()[0])
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError):
            pass

        # Update container-specific sizes
        usage.mcp.images = images_size
        usage.mcp.data += volumes_size

        return usage

    def deploy(self) -> bool:
        """Deploy container environment (install and create Dockerfile)."""
        # Call parent deploy for basic setup
        if not super().deploy():
            return False

        # Set up install directory for container assets
        install_dir = self.storage.install_dir()
        base_dir = install_dir / "base"
        base_dir.mkdir(parents=True, exist_ok=True)

        # Create Dockerfile for PyPI installation
        self._create_dockerfile(base_dir)

        return True

    def _create_dockerfile(self, base_dir: Path) -> None:
        """Copy Dockerfile template to build directory."""
        # Get the template Dockerfile from the runtime package
        template_path = Path(__file__).parent / "assets" / "Dockerfile"
        target_path = base_dir / "Dockerfile"

        # Copy the template (version is handled via build args)
        shutil.copy2(template_path, target_path)
