from __future__ import annotations
from importlib.metadata import version, PackageNotFoundError
import subprocess
from pathlib import Path


def is_development() -> bool:
    # cheap check, no branching elsewhere
    return (Path(__file__).resolve().parents[3] / ".git").exists()


def _git_describe() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "describe", "--dirty", "--always", "--tags"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        return out or None
    except Exception:
        return None


def get_version(dist_name: str = "vldmcp") -> str:
    # prefer installed dist version
    try:
        base = version(dist_name)
    except PackageNotFoundError:
        base = "0.0.0"

    # decorate if we're in a git checkout (pure cosmetics, NOT used for logic)
    if is_development():
        g = _git_describe()
        if g and g != base:
            return f"{base}+{g}"
    return base
