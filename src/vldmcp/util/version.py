import subprocess
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import vldmcp


def is_development() -> bool:
    # cheap check, no branching elsewhere
    return (Path(vldmcp.__file__).parent.parent.parent / ".git").exists()


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
