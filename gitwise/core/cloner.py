"""Clone (or reuse) a GitHub repo locally."""
import re
import shutil
import subprocess
from pathlib import Path

from gitwise.config import REPO_CACHE_DIR


class CloneError(Exception):
    pass


def repo_name_from_url(url: str) -> str:
    """https://github.com/tiangolo/fastapi -> tiangolo__fastapi"""
    match = re.search(r"github\.com/([^/]+)/([^/.]+)", url.rstrip("/"))
    if not match:
        raise CloneError(f"Could not parse a GitHub owner/repo from: {url}")
    owner, repo = match.groups()
    return f"{owner}__{repo}"


def clone_repo(url: str, force: bool = False) -> Path:
    """Clone the repo into the local cache dir, returns local path.

    If already cloned and force=False, reuses the existing checkout.
    """
    name = repo_name_from_url(url)
    dest = REPO_CACHE_DIR / name

    if dest.exists() and not force:
        return dest

    if dest.exists() and force:
        shutil.rmtree(dest)

    REPO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CloneError(f"git clone failed:\n{result.stderr}")

    return dest
