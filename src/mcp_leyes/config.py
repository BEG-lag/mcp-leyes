"""Settings from environment variables."""

from __future__ import annotations

import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SOURCE = "https://github.com/BEG-lag/leyes-mx.git"
DEFAULT_WEB_URL = "https://github.com/BEG-lag/leyes-mx"
_GITHUB = re.compile(r"^(?:https://|git@)github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$")


def default_cache_dir() -> Path:
    """~/.cache/mcp-leyes (XDG), ~/Library/Caches/mcp-leyes or %LOCALAPPDATA%\\mcp-leyes."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "mcp-leyes"
    if sys.platform == "darwin" and not os.environ.get("XDG_CACHE_HOME"):
        return Path.home() / "Library" / "Caches" / "mcp-leyes"
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "mcp-leyes"


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    cache_dir: Path
    source: str
    refresh_hours: float = 24.0
    web_url: str = DEFAULT_WEB_URL

    @classmethod
    def from_env(cls) -> Settings:
        source = os.environ.get("MCP_LEYES_SOURCE", "").strip() or DEFAULT_SOURCE
        if not re.match(r"^[a-z][a-z0-9+.-]*://|^git@", source):
            source = str(Path(source).expanduser().resolve())
        cache = os.environ.get("MCP_LEYES_CACHE", "").strip()
        web = os.environ.get("MCP_LEYES_WEB_URL", "").strip() or web_url_for(source)
        return cls(
            cache_dir=Path(cache).expanduser() if cache else default_cache_dir(),
            source=source,
            refresh_hours=max(0.0, _float_env("MCP_LEYES_REFRESH_HOURS", 24.0)),
            web_url=web.rstrip("/"),
        )

    @property
    def workdir(self) -> Path:
        """One directory per source, so a test fixture never mixes with the real data."""
        digest = hashlib.sha1(self.source.encode("utf-8")).hexdigest()[:10]
        name = re.sub(r"[^A-Za-z0-9]+", "-", self.source.rstrip("/").split("/")[-1])
        name = name.removesuffix("-git").strip("-") or "leyes"
        return self.cache_dir / f"{name}-{digest}"

    @property
    def repo_path(self) -> Path:
        return self.workdir / "repo.git"

    @property
    def index_path(self) -> Path:
        return self.workdir / "index.sqlite"


def web_url_for(source: str) -> str:
    m = _GITHUB.match(source)
    if m:
        return f"https://github.com/{m[1]}/{m[2]}"
    return DEFAULT_WEB_URL
